def insertion_sort(records,field,reverse=False):
    result=list(records)
    comparisons=0
    shifts=0
    for i in range(1,len(result)):
        current=result[i]
        j=i-1
        while j>=0:
            comparisons+=1
            if reverse:
                should_shift=result[j][field]<current[field]
            else:
                should_shift=result[j][field]>current[field]
            if not should_shift:
                break
            result[j+1]=result[j]
            shifts+=1
            j-=1
        result[j+1]=current

    return result,{"comparisons":comparisons,"shifts":shifts}

def merge_sort(records,field,reverse=False):
    stats={"comparisons":0,"recursive_calls":0}
    result=list(records)

    def merge(target,left,right):
        i=j=k=0
        while i<len(left) and j<len(right):
            stats["comparisons"]+=1
            if reverse:
                take_left=left[i][field]>=right[j][field]
            else:
                take_left=left[i][field]<=right[j][field]

            if take_left:
                target[k]=left[i]
                i+=1
            else:
                target[k]=right[j]
                j+=1
            k+=1

        while i<len(left):
            target[k]=left[i]
            i+=1
            k+=1
        while j<len(right):
            target[k]=right[j]
            j+=1
            k+=1
    def sort(items):
        stats["recursive_calls"]+=1
        n=len(items)
        if n<=1:
            return
        mid=n//2
        left=items[:mid]
        right=items[mid:]
        sort(left)
        sort(right)
        merge(items,left,right)
    sort(result)
    return result,stats

def compare_sorts(records, field, reverse=False):
    insertion_result, insertion_stats = insertion_sort(records, field, reverse)
    merge_result, merge_stats = merge_sort(records, field, reverse)

    return {
        "insertion": insertion_stats,
        "merge": merge_stats,
        "same_result": insertion_result == merge_result,
    }

