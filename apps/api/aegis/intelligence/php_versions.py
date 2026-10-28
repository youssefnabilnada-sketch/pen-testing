"""Conservative stable PHP inventory matching; never a runtime vulnerability verdict."""
import re

def match_php_cpe(version,affected):
    def stable(value):
        if not isinstance(value,str) or not re.fullmatch(r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)',value):raise ValueError()
        return tuple(map(int,value.split('.')))
    try:
        actual=stable(version)
        if affected.get('name')!='php:php':return None
        target=affected.get('version','*')
        bounds=affected.get('constraints',{})
        if not isinstance(bounds,dict):return None
        allowed={'versionStartIncluding','versionStartExcluding','versionEndIncluding','versionEndExcluding'}
        if set(bounds)-allowed:return None
        if not bounds and target in ('*','-'):return None
        comparisons=[]
        if target not in ('*','-'):comparisons.append(actual==stable(target))
        for key,value in bounds.items():
            boundary=stable(value)
            comparisons.append({'versionStartIncluding':actual>=boundary,'versionStartExcluding':actual>boundary,'versionEndIncluding':actual<=boundary,'versionEndExcluding':actual<boundary}[key])
        return all(comparisons)
    except (ValueError,TypeError):return None
