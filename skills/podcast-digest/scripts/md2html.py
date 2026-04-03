#!/usr/bin/env python3
"""Markdown → semantic HTML converter for Readwise Reader.

Usage:
    python3 md2html.py input.md > output.html
    python3 md2html.py input.md -o output.html
    
As module:
    from md2html import md_to_html
    html = md_to_html(markdown_string)

Rules:
- Headers → <h1>–<h3>, paragraphs → <p>, blockquotes → <blockquote>
- Bold **text** → <b>text</b>
- Horizontal rules --- → <hr>
- Numbered lists → <ol><li>, bullet lists → <ul><li>
- NEVER uses <br> for spacing
"""

import re
import sys
import argparse


def md_to_html(text: str) -> str:
    lines = text.split('\n')
    html_parts = []
    para_lines = []
    list_type = None  # 'ol' or 'ul' or None

    def flush_para():
        nonlocal para_lines
        if para_lines:
            html_parts.append('<p>' + ' '.join(para_lines) + '</p>')
            para_lines = []

    def flush_list():
        nonlocal list_type
        if list_type:
            html_parts.append(f'</{list_type}>')
            list_type = None

    def bold(s):
        return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)

    for line in lines:
        stripped = line.strip()

        if not stripped:
            flush_para()
            flush_list()
            continue

        if stripped == '---':
            flush_para()
            flush_list()
            html_parts.append('<hr>')
            continue

        h_match = re.match(r'^(#{1,3})\s+(.+)$', stripped)
        if h_match:
            flush_para()
            flush_list()
            level = len(h_match.group(1))
            html_parts.append(f'<h{level}>{bold(h_match.group(2))}</h{level}>')
            continue

        if stripped.startswith('> '):
            flush_para()
            flush_list()
            html_parts.append(f'<blockquote>{bold(stripped[2:])}</blockquote>')
            continue

        num_match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if num_match:
            flush_para()
            if list_type != 'ol':
                flush_list()
                html_parts.append('<ol>')
                list_type = 'ol'
            html_parts.append(f'<li>{bold(num_match.group(2))}</li>')
            continue

        bullet_match = re.match(r'^[-*]\s+(.+)$', stripped)
        if bullet_match:
            flush_para()
            if list_type != 'ul':
                flush_list()
                html_parts.append('<ul>')
                list_type = 'ul'
            html_parts.append(f'<li>{bold(bullet_match.group(1))}</li>')
            continue

        flush_list()
        para_lines.append(bold(stripped))

    flush_para()
    flush_list()
    return '\n'.join(html_parts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Markdown to semantic HTML')
    parser.add_argument('input', help='Input markdown file')
    parser.add_argument('-o', '--output', help='Output HTML file (default: stdout)')
    args = parser.parse_args()

    with open(args.input) as f:
        md = f.read()

    html = md_to_html(md)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(html)
    else:
        print(html)
