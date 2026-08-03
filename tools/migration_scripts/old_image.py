import os
import re

def update_image_paths_text_only():
    current_dir = os.getcwd()
    
    # 정규식 패턴: 썸네일 경로와 본문 이미지 경로 매칭
    thumbnail_pattern = re.compile(r'^(thumbnail:\s*)(.+)$', re.MULTILINE)
    image_pattern = re.compile(r'!\[(.*?)\]\((.+?)\)')
    
    # 바꿀 대상 텍스트와 새로운 텍스트
    old_path_prefix = "/images/"
    new_path_prefix = "/assets/images/old/"
    
    # 현재 폴더의 모든 파일 목록 가져오기
    for filename in os.listdir(current_dir):
        if not filename.lower().endswith('.md'):
            continue
            
        filepath = os.path.join(current_dir, filename)
        
        # 파일 읽기
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"[오류] 파일 읽기 실패 ({filename}): {e}")
            continue
            
        new_content = content
        
        # 1. 서문 썸네일 경로 텍스트 치환
        def replace_thumbnail(match):
            prefix = match.group(1) # 'thumbnail: ' 부분
            img_path = match.group(2).strip(' "\'')
            # 기존 경로에서 /images/ 부분만 교체
            new_img_path = img_path.replace(old_path_prefix, new_path_prefix, 1)
            return f"{prefix}{new_img_path}"
            
        # 2. 본문 이미지 경로 텍스트 치환
        def replace_image(match):
            alt_text = match.group(1) # '[]' 안의 텍스트
            img_path = match.group(2).strip(' "\'')
            # 기존 경로에서 /images/ 부분만 교체
            new_img_path = img_path.replace(old_path_prefix, new_path_prefix, 1)
            return f"![{alt_text}]({new_img_path})"
            
        # 텍스트 치환 실행
        new_content = thumbnail_pattern.sub(replace_thumbnail, new_content)
        new_content = image_pattern.sub(replace_image, new_content)
        
        # 변경된 내용이 있을 경우에만 덮어쓰기
        if new_content != content:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"[성공] 텍스트 경로 치환 완료: {filename}")
            except Exception as e:
                print(f"[실패] 파일 저장 오류 ({filename}): {e}")
        else:
            print(f"[스킵] 변경할 대상이 없음: {filename}")

if __name__ == "__main__":
    print("마크다운 이미지 경로 텍스트 수정을 시작합니다...\n")
    update_image_paths_text_only()
    print("\n작업이 완료되었습니다.")