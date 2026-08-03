import os
import re
import csv

def replace_markdown_tags():
    current_dir = os.getcwd()
    
    # 1. 현재 폴더에서 CSV 파일 찾기
    csv_files = [f for f in os.listdir(current_dir) if f.lower().endswith('.csv')]
    
    if not csv_files:
        print("[오류] 현재 폴더에 CSV 파일이 없습니다. 매핑할 CSV 파일을 준비해주세요.")
        return
        
    csv_path = os.path.join(current_dir, csv_files[0])
    print(f"[{csv_files[0]}] 파일을 기준으로 태그 치환을 시작합니다.")
    
    # 2. CSV 파일을 읽어서 변환용 딕셔너리 생성
    tag_map = {}
    try:
        # utf-8-sig를 사용하여 BOM이 포함된 CSV(엑셀에서 저장한 파일 등)도 안전하게 처리
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    old_tag = row[0].strip()
                    new_tag = row[1].strip()
                    tag_map[old_tag] = new_tag
    except Exception as e:
        print(f"[오류] CSV 파일을 읽는 중 문제가 발생했습니다: {e}")
        return
        
    if not tag_map:
        print("[경고] CSV 파일에서 읽어온 태그 매핑 데이터가 없습니다.")
        return

    # 3. 마크다운 파일 순회 및 태그 치환
    # tags: [...] 형태의 배열 전체를 잡아내는 정규식
    tags_pattern = re.compile(r'^(tags:\s*\[)(.*?)(\])', re.MULTILINE)
    
    for filename in os.listdir(current_dir):
        if not filename.lower().endswith('.md'):
            continue
            
        filepath = os.path.join(current_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"[오류] 파일 읽기 실패 ({filename}): {e}")
            continue
            
        # 태그 배열 내부에서 개별 태그를 치환하는 함수
        def tag_replacer(match):
            prefix = match.group(1)       # 'tags: ['
            tags_content = match.group(2) # '"csharp", "UE5"'
            suffix = match.group(3)       # ']'
            
            # 따옴표 안의 텍스트만 치환하는 내부 함수
            def single_tag_replacer(t_match):
                quote = t_match.group(1)    # '"' 또는 "'"
                tag_name = t_match.group(2) # 'csharp'
                
                # CSV에서 읽어온 딕셔너리에 존재하면 변경, 없으면 원본 유지
                new_tag_name = tag_map.get(tag_name, tag_name)
                return f"{quote}{new_tag_name}{quote}"
            
            # 배열 내용물 안에서 정규식으로 따옴표 쌍을 찾아 치환
            new_tags_content = re.sub(r'([\"\'])(.*?)\1', single_tag_replacer, tags_content)
            return f"{prefix}{new_tags_content}{suffix}"
            
        new_content = tags_pattern.sub(tag_replacer, content)
        
        # 원본과 비교해 변경된 내용이 존재할 경우에만 덮어쓰기
        if new_content != content:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"[성공] 태그 치환 완료: {filename}")
            except Exception as e:
                print(f"[실패] 파일 저장 오류 ({filename}): {e}")

if __name__ == "__main__":
    print("마크다운 태그 일괄 치환 작업을 시작합니다...\n")
    replace_markdown_tags()
    print("\n작업이 완료되었습니다.")