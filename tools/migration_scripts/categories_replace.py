import os
import re
import csv

def replace_markdown_categories():
    current_dir = os.getcwd()
    
    # 1. 현재 폴더에서 CSV 파일 찾기
    csv_files = [f for f in os.listdir(current_dir) if f.lower().endswith('.csv')]
    
    if not csv_files:
        print("[오류] 현재 폴더에 CSV 파일이 없습니다. 매핑할 CSV 파일을 준비해주세요.")
        return
        
    csv_path = os.path.join(current_dir, csv_files[0])
    print(f"[{csv_files[0]}] 파일을 기준으로 카테고리 치환을 시작합니다.")
    
    # 2. CSV 파일을 읽어서 변환용 딕셔너리 생성
    category_map = {}
    try:
        # utf-8-sig를 사용하여 BOM이 포함된 CSV도 안전하게 처리
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    old_cat = row[0].strip()
                    new_cat = row[1].strip()
                    category_map[old_cat] = new_cat
    except Exception as e:
        print(f"[오류] CSV 파일을 읽는 중 문제가 발생했습니다: {e}")
        return
        
    if not category_map:
        print("[경고] CSV 파일에서 읽어온 매핑 데이터가 없습니다.")
        return

    # 3. 마크다운 파일 순회 및 카테고리 치환
    # categories: [...] 형태의 배열 전체를 잡아내는 정규식
    categories_pattern = re.compile(r'^(categories:\s*\[)(.*?)(\])', re.MULTILINE)
    
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
            
        # 카테고리 배열 내부 치환 함수
        def category_replacer(match):
            prefix = match.group(1)       # 'categories: ['
            cats_content = match.group(2) # 'TPSProject' 또는 '"Unity", "Csharp"'
            suffix = match.group(3)       # ']'
            
            # 쉼표로 분리하여 개별 요소를 리스트화
            items = cats_content.split(',')
            new_items = []
            
            for item in items:
                stripped_item = item.strip()
                if not stripped_item:
                    continue
                    
                # 따옴표가 있는지 확인하여 제거 후 순수 텍스트만 추출
                has_quotes = False
                quote_char = ''
                if stripped_item.startswith(('"', "'")) and stripped_item.endswith(('"', "'")):
                    has_quotes = True
                    quote_char = stripped_item[0]
                    clean_name = stripped_item[1:-1]
                else:
                    clean_name = stripped_item
                    
                # CSV에서 읽어온 딕셔너리에 존재하면 변경, 없으면 원본 유지
                new_name = category_map.get(clean_name, clean_name)
                
                # 원래 따옴표가 있었다면 다시 붙여서 복구
                if has_quotes:
                    new_items.append(f"{quote_char}{new_name}{quote_char}")
                else:
                    new_items.append(new_name)
                    
            # 쉼표와 공백으로 다시 결합
            new_cats_content = ", ".join(new_items)
            return f"{prefix}{new_cats_content}{suffix}"
            
        new_content = categories_pattern.sub(category_replacer, content)
        
        # 원본과 비교해 변경된 내용이 존재할 경우에만 덮어쓰기
        if new_content != content:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"[성공] 카테고리 치환 완료: {filename}")
            except Exception as e:
                print(f"[실패] 파일 저장 오류 ({filename}): {e}")

if __name__ == "__main__":
    print("마크다운 카테고리 일괄 치환 작업을 시작합니다...\n")
    replace_markdown_categories()
    print("\n작업이 완료되었습니다.")