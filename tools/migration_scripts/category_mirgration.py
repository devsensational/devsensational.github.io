import os
import re

def process_frontmatter(fm):
    """
    Frontmatter 문자열을 줄 단위로 분석하여 series 블록을 categories로 변환합니다.
    """
    lines = fm.split('\n')
    new_lines = []
    in_series_block = False
    series_name = None
    
    for line in lines:
        # 'series:' 항목 시작 여부 확인 (앞뒤 공백 제거 후 비교)
        if line.strip() == 'series:':
            in_series_block = True
            continue
        
        if in_series_block:
            # 들여쓰기(공백, 탭 등)가 되어 있는 경우 series의 하위 항목으로 간주
            if re.match(r'^\s+', line) and line.strip() != '':
                # 하위 항목 중 'name:'이 포함된 줄에서 값 추출
                if re.search(r'^\s*name:', line):
                    # 'name:' 글자를 제거하고 실제 값만 추출
                    series_name = re.sub(r'^\s*name:\s*', '', line).strip()
                continue  # series 하위 항목의 원본 줄은 새 리스트에 추가하지 않음(삭제 효과)
            else:
                # 들여쓰기가 끝났다면 series 블록이 종료된 것임
                in_series_block = False
                # 추출한 name 값이 존재하면 categories 형식으로 추가
                if series_name:
                    new_lines.append(f"categories: [{series_name}]")
                    series_name = None
                
                # 현재 줄(series 밖의 항목)은 그대로 추가
                new_lines.append(line)
        else:
            # series 블록 밖의 일반 항목들은 그대로 추가
            new_lines.append(line)
            
    # 만약 문서 서문의 가장 마지막이 series 항목으로 끝났을 경우를 대비한 처리
    if in_series_block and series_name:
        new_lines.append(f"categories: [{series_name}]")
        
    return '\n'.join(new_lines)

def modify_markdown_series_to_categories():
    current_dir = os.getcwd()
    
    for filename in os.listdir(current_dir):
        if not filename.lower().endswith('.md'):
            continue
            
        filepath = os.path.join(current_dir, filename)
        
        # 파일 읽기
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
        except Exception as e:
            print(f"[오류] 파일 읽기 실패 ({filename}): {e}")
            continue
            
        # 최상단의 Frontmatter(--- 와 --- 사이) 영역만 추출
        match = re.match(r'^(---\n)(.*?)(\n---)', content, re.DOTALL)
        if not match:
            print(f"[스킵] Frontmatter(---) 영역을 찾을 수 없음: {filename}")
            continue
            
        start_dash = match.group(1)
        frontmatter = match.group(2)
        end_dash = match.group(3)
        
        # 서문 내용 수정 진행
        new_frontmatter = process_frontmatter(frontmatter)
        
        # 변경사항이 존재할 경우에만 파일 덮어쓰기
        if new_frontmatter != frontmatter:
            new_content = start_dash + new_frontmatter + end_dash + content[match.end():]
            try:
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                print(f"[성공] categories 변환 완료: {filename}")
            except Exception as e:
                print(f"[실패] 파일 쓰기 오류 ({filename}): {e}")
        else:
            print(f"[스킵] series 항목이 없거나 변경 대상이 아님: {filename}")

if __name__ == "__main__":
    print("마크다운 서문(Frontmatter) 수정 작업을 시작합니다...\n")
    modify_markdown_series_to_categories()
    print("\n작업이 완료되었습니다.")