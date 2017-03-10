#!/usr/bin/env python
# -*- coding: utf-8 -*-
# auto generate blog posts and blog nav page and doc page for PingCAP site
# created by gyy

import re
import sys
import datetime
import time
import pytz
from os import listdir, mkdir, remove
from os.path import isfile, isdir, join
from jinja2 import Template, Environment, PackageLoader

import markdown
from markdown.extensions.headerid import HeaderIdExtension
from mdx_gfm import GithubFlavoredMarkdownExtension

from feedgen.feed import FeedGenerator

import shutil


env = Environment(loader=PackageLoader('gen', '.'))

# delete all html file in dist
def clean_gen_html():
    for dir_name in ['../dist', '../dist/doc', '../dist/blog']:
        if not isdir(dir_name): mkdir(dir_name)

    doc_htmls, blog_htmls = [f for f in listdir('../dist/doc')], [f for f in listdir('../dist/blog')]
    htmls_dir_map = [(doc_htmls, '../dist/doc'), (blog_htmls, '../dist/blog')]

    for index in range(len(htmls_dir_map)):
        htmls, dirpath = htmls_dir_map[index]
        if htmls:
            for f in htmls:
                if isfile(join(dirpath, f)) and f.endswith('.html'):
                    remove(join(dirpath, f))

# a better assert
def check(cond, msg):
    if not cond:
        sys.stderr.write(msg)
        sys.stderr.flush()
        sys.exit(-1)

# generatd header unique id
def gen_header_id(val, separator):
    val = re.sub(u'[^a-zA-Z0-9\\.\u4e00-\u9fa5]+', ' ', val.lower())
    return '-'.join(val.strip().split(' '))

# md to html
def to_md(content):
    md = markdown.Markdown(extensions=[GithubFlavoredMarkdownExtension(), HeaderIdExtension(slugify=gen_header_id)])
    html = md.convert(content)
    return html

def parse_post(content, ty='blog'):
    if ty is 'blog':
        # parse blog post content
        txt = re.findall(r'\%\%(.*)\%\%', content, re.DOTALL)
        check(len(txt)==1, 'content error')
        cont = txt[0]

        # parse meta data
        meta_list = re.findall(r'\%(.*):(.*)\%', content, re.MULTILINE)

        post = dict(meta_list)
        post['content'] = cont.strip()
    else: # parse doc post content
        post = {}
        post['content'] = content.strip()
        # print content.strip()
        post['title'] = re.search(r'^#(.*)', content.strip()).group(1)
    return post

# walk current directory, return all markdown documents
def get_post_list(ty='blog'):
    file_dir = join('.', ty)
    zh_dir, en_dir = join(file_dir, 'zh_cn'), join(file_dir, 'en')

    if not isdir(zh_dir) and isdir(join(file_dir, 'zh')):
        zh_dir = join(file_dir, 'zh') # if has zh dir , replace 'zh_cn' to 'zh'

    # first element is list array for zh_cn post, second element is list of en post
    return [
            [join(zh_dir, f) for f in listdir(zh_dir) if isfile(join(zh_dir, f)) and f.endswith('.md')],
            [join(en_dir, f) for f in listdir(en_dir) if isfile(join(en_dir, f)) and f.endswith('.md')]
            ]

def parse_posts(ty='blog'):

    def _get_parsed_post(fname, ty, lang='zh'):
        with open(fname) as fp:
            c = fp.read().decode('utf-8')
            post = parse_post(c, ty)

            ## change all path for image to '/image/xxx.png' ##
            # re.findall(r'<img\s+?(?:alt=".*?")?\s+?src="\s*[^\s]*/([^\s]*?)\s*"\s*/>', post['content'])
            post['content'] = re.sub(r'!\[(.*?)\]\(\s*?[^\s]*/([^\s]*?)\)', r'![\1](/images/\2)', post['content'])
            ## change all img path end ##

            # change all path for xxx.md#xxx to {doc, blog}-xxx-{zh-cn}.html#xxxx
            if ty is 'blog':
                if lang is 'zh':
                    post['content'] = re.sub(r'\[(.*?)\]\(\s*?[^\s]+/([^\s]*?)\.md([^\s]*)\)', r'[\1](blog-\2-zh.html\3)', post['content'])
                else:
                    post['content'] = re.sub(r'\[(.*?)\]\(\s*?[^\s]+/([^\s]*?)\.md([^\s]*)\)', r'[\1](blog-\2.html\3)', post['content'])
            else:
                if lang is 'zh':
                    post['content'] = re.sub(r'\[(.*?)\]\(\s*?[^\s]+/([^\s]*?)\.md([^\s]*)\)', r'[\1](doc-\2-zh.html\3)', post['content'])
                else:
                    post['content'] = re.sub(r'\[(.*?)\]\(\s*?[^\s]+/([^\s]*?)\.md([^\s]*)\)', r'[\1](doc-\2.html\3)', post['content'])
            ## change all md path end ##

            '''
            re_obj = re.compile(r'\[.*?\]\(((.*?)\.md#{0,1}.*?)\)')
            md_links = re_obj.findall(post['content'])
            # mdLinks eg:
            # [(u'../overview.md#tidb-\u6574\u4f53\u67b6\u6784', u'../overview'), (u'../op-guide/recommendation.md', u'../op-guide/recommendation')]
            for md_link in md_links:
                raw_link, raw_link_name = md_link[0], re.findall(r'[a-z_\-A-Z0-9]+', md_link[1])[-1]
                ahchor =  re.findall(r'#(.*)', raw_link)
                ahchor = ahchor[0] if ahchor else ''

                html_link = raw_link_name
                if lang is 'zh':
                    html_link += '-zh'
                html_link = ty + '-' + html_link + '.html'

                md_fragement = re.findall(r'(.*\.md)#{0,1}.*?', raw_link)[0]
                post['content'] = re.sub(re.escape(md_fragement), re.escape(html_link), post['content'])
            '''

            post[ty + '_html'] = to_md(post['content']) #html content
            post['filename'] = fname.split('/')[-1].split('.md')[0]
        return post

    posts = [[], []] # posts[0] is zh post list, posts[1] is en post list
    zh_files, en_files  = get_post_list(ty)

    years_zh, years_en = {}, {}

    # ergodic for get all parsed post object
    for fname in zh_files:
            post = _get_parsed_post(fname, ty)
            post['html_filename'] = ty + '-' + post['filename'] + '-zh.html'

            if re.sub(r'zh_cn', r'en', fname) in en_files:

                post['lang_filename'] = ty + '-' + post['filename'] + '.html'
                posts[0].append(post)

                en_post = _get_parsed_post(re.sub(r'zh_cn', r'en', fname), ty, 'en')
                en_post['html_filename'] = ty + '-' + post['filename'] + '.html'
                en_post['lang_filename'] = ty + '-' + post['filename'] + '-zh.html'

                posts[1].append(en_post)
            else:
                post['lang_filename'] = '404.html'
                posts[0].append(post)

    if ty is 'blog': # get blog nav list object
        years_zh, years_en = gen__years(posts[0]), gen__years(posts[1])
        tpl_name_suffix = 'blog.html.tpl'
    else:
        tpl_name_suffix = 'doc.html.tpl'

    # gen html for chinese posts
    for post in posts[0]:
        tpl_name = 'zh.' + tpl_name_suffix
        gen_post_html(tpl_name, join('..', 'dist', ty, post['html_filename']), post, years_zh)

    # gen html for en posts
    if len(posts[1]):
        for post in posts[1]:
            tpl_name = 'en.' + tpl_name_suffix
            gen_post_html(tpl_name, join('..', 'dist', ty, post['html_filename']), post, years_en)
            # sorted(posts, key=lambda post: post['create_at'], reverse=True)
    return posts

def gen_html(tpl, out_file, userdict):
    template = env.get_template(tpl)

    html = template.render(userdict)
    with open(out_file, 'w') as fp:
        fp.write(html.encode('utf-8'))
        fp.flush()

def gen_post_html(tpl, out_file,  post,  years = {}):
    return gen_html(tpl, out_file, {'post': post, 'years': years})

def gen_blog_list_html(posts):
    p = []
    for post in posts:
        dt = datetime.datetime.strptime(post['create_at'], '%Y-%m-%d')
        post['ts'] = time.mktime(dt.timetuple())
        p.append(post)
    posts = sorted(p,  key = lambda x: -x['ts'])
    return gen_html('bloglist.html.tpl', '../bloglist.html', {'posts':posts})

def gen__years(posts):
    if not posts: return

    years = { 'ys': [] }

    for post in posts:
        dt = str(datetime.datetime.strptime(post['create_at'], '%Y-%m-%d'))
        create_year, create_month, create_day = re.search(r'(\d{4})-(\d{2})-(\d{2})', dt).group().split('-')

        if not create_year in years:
            years['ys'].append(create_year)
            years[create_year] = { 'post_count': 0, 'zh_code': create_year, 'months': [] }

        if not create_month in years[create_year]:
            years[create_year]['months'].append(create_month)
            years[create_year][create_month] = { 'zh_code': str(create_month)+u'月', 'posts': [], 'post_count': 0 }

        years[create_year]['post_count'] += 1
        years[create_year][create_month]['post_count'] += 1

        years[create_year][create_month]['posts'].append({'day': create_day, 'title': post['title'], 'href': post['html_filename']})

    years['ys'] = sorted(years['ys'], reverse=True)
    for year in years['ys']:
        years[year]['months'] = sorted(years[year]['months'], reverse=True)
    max_year = max(years['ys'])
    max_month = max(years[max_year]['months'])

    years[max_year]['show'] = True
    years[max_year][max_month]['show'] = True

    return years

def gen_feed(posts):
    fg = FeedGenerator()
    tz = pytz.timezone('Asia/Shanghai')
    fg.id('http://www.pingcap.com/bloglist.html')
    fg.title('PingCAP Blog')
    fg.updated(datetime.datetime.now(tz))
    for post in posts:
        fe = fg.add_entry()
        fe.id('http://pingcap.com/' + post['html_filename'])
        fe.title(post['title'])
        dt = datetime.datetime.strptime(post['create_at'], '%Y-%m-%d')
        dt = dt.replace(tzinfo=tz)
        fe.updated(dt)
        fe.content(post['blog_html'], type='html')
    result = fg.atom_str()
    with open("../rss.xml", 'w') as fp:
        fp.write(result)
        fp.flush()

if __name__ == '__main__':
    print 'clean...'
    clean_gen_html()
    print 'clean over...'
    time.sleep(1)
    print 'start gen html'
    posts = parse_posts()

    posts = parse_posts('doc')
    print 'successfully!'
    #gen_feed(posts)
