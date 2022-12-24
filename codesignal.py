def solution(n):
    print(str(type(n)))
    if str(type(n)) == "int":
        return n % 2
    else:
        return -1
print(solution(15))