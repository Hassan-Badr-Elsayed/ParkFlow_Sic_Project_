import pandas as pd

COLUMNS=["session_id","plate","vehicle_type", "space_id",
           "entry_time", "exit_time", "duration_min", "fee"]

def build_dataframe(records):
    return pd.DataFrame(records, columns=COLUMNS)

def clean_sessions(df):
    rows_in =len(df)
    df=df.copy()

    df["entry_time"]=pd.to_datetime(df["entry_time"],errors="coerce")
    df["exit_time"]=pd.to_datetime(df["exit_time"],errors="coerce")
    df["duration_min"]=pd.to_numeric(df["duration_min"],errors="coerce")
    df["fee"]=pd.to_numeric(df["fee"],errors="coerce")


    df=df.dropna(subset=["entry_time","exit_time"])
    calc=(df["exit_time"]-df["entry_time"]).dt.total_seconds()/60
    df["duration_min"]=df["duration_min"].fillna(calc)
    df=df[df["exit_time"]>=df["entry_time"]]
    df=df[df["duration_min"]>=0]
    df=df.dropna(subset=["plate"])
    df["plate"]=df["plate"].astype(str).str.strip().str.upper()
    df=df[df["plate"].str.match(r"^[A-Z0-9]{3,8}$")]

    report={"rows_in":rows_in,"rows_dropped":rows_in-len(df)}
    return df,report

def entries_per_hour(df):
    hours=df["entry_time"].dt.hour
    return hours.value_counts().sort_index()

def entries_per_day(df):
    days=df["entry_time"].dt.date
    return days.value_counts().sort_index()

def avg_stay_hours_by_type(df):
    return df.groupby("vehicle_type")["duration_min"].mean()/60

def usage_by_floor(df):
   floors=df["space_id"].str.split("-").str[0]
   return floors.value_counts().sort_index()

def revenue_by_day(df):
    valid_fees=df[df["fee"].notna()&(df["fee"]>=0)]

    return valid_fees.groupby(valid_fees["entry_time"].dt.date)["fee"].sum()

def summary_metrics(df):
    if df.empty:
        return {"total_sessions": 0, "total_revenue": 0.0, "avg_stay_hours": 0.0}
    fees = df["fee"].dropna()
    fees = fees[fees >= 0]
    return {
        "total_sessions": len(df),
        "total_revenue": float(fees.sum()),
        "avg_stay_hours": float(df["duration_min"].mean() / 60),
    }

def get_insights(df):
    insights=[]
    if df.empty:
        return ["No data available"]


    valid_hours=entries_per_hour(df)
    if not valid_hours.empty:
        peak_hour=valid_hours.idxmax()
        insights.append(f"Peak hour is {peak_hour:02d}:00")


    valid_floors=usage_by_floor(df)
    if not valid_floors.empty:
         top_floor=valid_floors.idxmax()
         insights.append(f"Floor {top_floor} is used most")


    valid_types=df["vehicle_type"].dropna()
    if not valid_types.empty:
         top_type=valid_types.value_counts().idxmax()
         insights.append(f"Most used type is {top_type}")

    daily_revenue = revenue_by_day(df)
    if not daily_revenue.empty:
        best_day = daily_revenue.idxmax()
        best_revenue = daily_revenue.max()

        insights.append(
            f"Highest revenue day is {best_day} "
            f"with revenue {best_revenue:.2f}")

    if not insights:
        return ["No valid data available"]

    return insights



