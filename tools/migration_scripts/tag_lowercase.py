import os
import re

def lowercase_md_tags():
    # 현재 폴더의 모든 파일 탐색
    for filename in os.listdir('.'):
        if not filename.endswith('.md'):
            continue

        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()

        # 최상단 서문(Front-matter) 영역만 추출 (--- 와 --- 사이)
        match = re.match(r'^(---\n)(.*?)(\n---)', content, re.DOTALL)
        if not match:
            continue

        frontmatter = match.group(2)

        # 서문 내에서 tags: [...] 라인을 찾아 내부 문자열을 소문자로 변환하는 함수
        def lower_tags(tag_match):
            full_tag_line = tag_match.group(0)
            
            # 따옴표 안에 있는 문자열만 찾아 소문자로 변환
            def make_lower(string_match):
                return string_match.group(0).lower()
            
            # 쌍따옴표(") 또는 홑따옴표(')로 감싸진 문자열 타겟팅
            lowercased_line = re.sub(r'["\'][^"\']+["\']', make_lower, full_tag_line)
            return lowercased_line

        # 정규식을 이용해 tags: 배열 라인 교체 (다중 라인 매칭 활성화)
        new_frontmatter = re.sub(r'^tags:\s*\[.*?\]', lower_tags, frontmatter, flags=re.MULTILINE)

        # 변경 사항이 있을 경우에만 파일 덮어쓰기
        if frontmatter != new_frontmatter:
            new_content = content[:match.start(2)] + new_frontmatter + content[match.end(2):]
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f"[Success] {filename} 태그 소문자 변환 완료!")
        else:
            print(f"[Skip] {filename} (이미 소문자이거나 변경 사항 없음)")

if __name__ == '__main__':
    print("🚀 마크다운 태그 소문자 변환 작업을 시작합니다...")
    lowercase_md_tags()
    print("✅ 모든 작업이 완료되었습니다!")