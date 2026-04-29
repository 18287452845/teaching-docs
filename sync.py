"""
同步 Obsidian 笔义到 docs-site
用法:
  python sync.py          # 同步内容（已有文件不动，只更新内容）
  python sync.py --show   # 查看中英文对照关系

已有文件保持原 ASCII 文件名不变，只同步 md 内容和 frontmatter。
新增文件自动生成 ASCII 文件名，映射写入 mapping.json。
"""
import os, re, json, sys

VAULT   = r'C:\Users\admin\Documents\tnote\tnote\课程讲义'
DOCS    = r'C:\Users\admin\Documents\tnote\docs-site\src\content\docs'
MAPPING = r'C:\Users\admin\Documents\tnote\docs-site\mapping.json'

DIR_MAP = {
    'Windows 服务器安全配置': 'windows-server-security',
    '数据库系统管理和运维': 'database-admin',
    '01 项目一 走进Windows服务器': '01-intro',
    '实验三 数据': 'lab3-data-sub',
}

def load_mapping():
    if os.path.exists(MAPPING):
        with open(MAPPING, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_mapping(mapping):
    with open(MAPPING, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

def ascii_dir(rel_dir):
    parts = rel_dir.replace(os.sep, '/').split('/')
    return '/'.join(DIR_MAP.get(p, p) for p in parts)

def to_ascii_name(text):
    name = text.replace('.md', '')
    num = ''
    m = re.match(r'^(\d+)', name)
    if m:
        num = m.group(1)
        name = name[len(num):].lstrip(' .-_')
    name = re.sub(r'[^\w]', '-', name).strip('-')
    name = re.sub(r'-+', '-', name).lower()
    if num and not name.startswith(f'{num}-'):
        name = f'{num}-{name}'
    return (name or 'untitled') + '.md'

def resolve_dst(src_dir, fn, mapping):
    """根据 Obsidian 源文件，找到 docs-site 中的目标路径"""
    rel_dir = os.path.relpath(src_dir, VAULT)
    ascii_dirs = ascii_dir(rel_dir)
    key = f'{rel_dir}/{fn}'

    # 1. mapping.json 中已有
    if key in mapping:
        return os.path.join(DOCS, ascii_dirs, mapping[key])

    # 2. 目标目录下已有同内容的文件（按 frontmatter title 匹配）
    src_file = os.path.join(src_dir, fn)
    target_dir = os.path.join(DOCS, ascii_dirs)
    if os.path.isdir(target_dir):
        with open(src_file, 'r', encoding='utf-8') as f:
            src_title_m = re.match(r'^#\s+(.+)', f.read(), re.MULTILINE)
        src_title = src_title_m.group(1).strip() if src_title_m else None
        if src_title:
            for existing_fn in os.listdir(target_dir):
                if not existing_fn.endswith('.md'):
                    continue
                existing_path = os.path.join(target_dir, existing_fn)
                with open(existing_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                if f'title: {src_title}' in first_line or f'title:{src_title}' in first_line:
                    return existing_path

    # 3. 新文件：自动生成 ASCII 名
    ascii_fn = to_ascii_name(fn)
    mapping[key] = ascii_fn
    return os.path.join(DOCS, ascii_dirs, ascii_fn)

def show_mapping(mapping):
    # 扫描 docs-site 中的实际文件，从 frontmatter 提取中文 title
    print('\n' + '=' * 70)
    print(f'  {"侧边栏显示名 (title)".center(30)}  {"ASCII 文件名 (路由)".center(36)}')
    print('=' * 70)
    entries = []
    for dirpath, dirnames, filenames in os.walk(DOCS):
        for fn in filenames:
            if not fn.endswith('.md') or fn == 'index.mdx':
                continue
            fpath = os.path.join(dirpath, fn)
            rel = os.path.relpath(fpath, DOCS)
            title = rel  # fallback
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    m = re.match(r'^---\ntitle:\s*(.+)', f.read())
                if m:
                    title = m.group(1)
            except:
                pass
            entries.append((title, rel))
    entries.sort()
    for title, rel in entries:
        print(f'  {title:<32} {rel:<40}')
    print('=' * 70)
    print(f'  共 {len(entries)} 个文件\n')

def sync(mapping):
    updated = 0
    skipped = 0
    new_mapped = []

    for dirpath, dirnames, filenames in os.walk(VAULT):
        for fn in filenames:
            if not fn.endswith('.md'):
                continue
            src_file = os.path.join(dirpath, fn)
            dst_file = resolve_dst(dirpath, fn, mapping)

            # 比较修改时间
            if os.path.exists(dst_file):
                if os.path.getmtime(src_file) <= os.path.getmtime(dst_file):
                    skipped += 1
                    continue
            else:
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                new_mapped.append(f'{fn} -> {os.path.basename(dst_file)}')

            # 读取原始内容
            with open(src_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 保留已有 frontmatter 的 title
            existing_title = None
            if os.path.exists(dst_file):
                with open(dst_file, 'r', encoding='utf-8') as f:
                    old = f.read(500)
                m = re.match(r'^---\ntitle:\s*(.+)', old)
                if m:
                    existing_title = m.group(1)

            title = existing_title
            if not title:
                m = re.match(r'^#\s+(.+)', content, re.MULTILINE)
                title = m.group(1).strip() if m else fn

            with open(dst_file, 'w', encoding='utf-8') as f:
                f.write(f'---\ntitle: {title}\n---\n\n{content}')

            updated += 1

    if new_mapped:
        print('  [新文件自动映射]')
        for item in new_mapped:
            print(f'    {item}')
        print('  如需改名，编辑 mapping.json 后重新运行')
        save_mapping(mapping)

    print(f'\nDone: {updated} updated, {skipped} skipped')
    if updated > 0:
        print('Next:')
        print('  cd C:\\Users\\admin\\Documents\\tnote\\docs-site')
        print('  git add -A && git commit -m "update: sync notes" && git push origin master')

if __name__ == '__main__':
    mapping = load_mapping()
    if '--show' in sys.argv:
        show_mapping(mapping)
    else:
        sync(mapping)
