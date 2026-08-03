import os
import re

def get_safe_filename(title):
    """
    윈도우 파일명에 사용할 수 없는 특수문자를 제거합니다.
    """
    return re.sub(r'[\\/*?:"<>|]', "", title).strip()

def rename_markdown_files():
    # 스크립트가 실행된 현재 폴더 경로
    current_dir = os.getcwd()
    
    # 현재 폴더의 모든 파일 목록 가져오기
    for filename in os.listdir(current_dir):
        if not filename.lower().endswith('.md'):
            continue
            
        filepath = os.path.join(current_dir, filename)
        
        # 파일 읽기 (UTF-8 인코딩)
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
        except Exception as e:
            print(f"파일을 읽는 중 오류 발생 ({filename}): {e}")
            continue
            
        # 정규식을 사용하여 --- 사이의 Frontmatter 부분 추출
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            print(f"Frontmatter(---)를 찾을 수 없음 스킵: {filename}")
            continue
            
        frontmatter = frontmatter_match.group(1)
        
        # title과 date 값 추출
        title_match = re.search(r'^title:\s*(.+)$', frontmatter, re.MULTILINE)
        date_match = re.search(r'^date:\s*(.+)$', frontmatter, re.MULTILINE)
        
        if title_match and date_match:
            # 값의 앞뒤 공백 및 따옴표 제거
            raw_title = title_match.group(1).strip(' "\'')
            raw_date = date_match.group(1).strip(' "\'')
            
            # YYYY-MM-DD 형식 추출 (예: 2025-06-30T08:35:15... -> 2025-06-30)
            date_iso_match = re.search(r'(\d{4}-\d{2}-\d{2})', raw_date)
            
            if date_iso_match:
                date_formatted = date_iso_match.group(1)
                safe_title = get_safe_filename(raw_title)
                
                # 새 파일명 생성: YYYY-MM-DD-TITLE.md
                new_filename = f"{date_formatted}-{safe_title}.md"
                new_filepath = os.path.join(current_dir, new_filename)
                
                # 기존 파일명과 새 파일명이 다르고, 동일한 이름의 파일이 존재하지 않을 때만 변경
                if filepath != new_filepath:
                    if not os.path.exists(new_filepath):
                        try:
                            os.rename(filepath, new_filepath)
                            print(f"[성공] {filename} -> {new_filename}")
                        except Exception as e:
                            print(f"[실패] 이름 변경 오류 ({filename}): {e}")
                    else:
                        print(f"[스킵] 동일한 이름의 파일이 이미 존재함: {new_filename}")
            else:
                print(f"[스킵] 날짜 형식을 인식할 수 없음: {filename}")
        else:
            print(f"[스킵] title 또는 date 항목이 없음: {filename}")

if __name__ == "__main__":
    print("마크다운 파일명 변경 작업을 시작합니다...\n")
    rename_markdown_files()
    print("\n작업이 완료되었습니다.")