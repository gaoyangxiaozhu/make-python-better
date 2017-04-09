
import re

lines = None
###
# dir_level is the current dir level, default start from 0
# argument `line_num` is the current line num, initial value is 0
# tab_num is 1/2 of the number of spacer for each line 
# for 0 dir_level, the space number at the start of line is 0
# for 1 dir_level, the space number at the start of line is 2, so the value of tab_num is 1
# and so on...
###

global_category = { 'name' : '__global__', 'categories': [], 'posts': [] }
def get_directory(dir_level, line_num):
    categories = []
    category = {}
    while line_num <  len(lines):
        #print  'currnet  line num  is ',  line_num
        line = lines[line_num]
        if line.strip() == '': line_num += 1; continue
        if re.match('^\s*\+\s+', line): # if current line corresponding to a category name
            #print 'category ', line
            tab, category_name  = re.findall(r'^(\s*)\+\s+(.*)', line)[0]
            tab_num = len(tab) / 2
            
            if tab_num == dir_level:
                category = { 'name' : category_name, 'posts': [], 'categories': [] }
                categories.append(category)
            if tab_num == dir_level + 1:
                #print 'enter sub ' + category_name +' directory'
                append_categories, next_dir_level, next_start_line_num = get_directory(dir_level + 1, line_num)
                category['categories'] += append_categories
                #print category['categories']
                #print 'out '
                #print 'next_dir_level ', next_dir_level, ' dir_level ', dir_level
                #print 'next start line is  ', next_start_line_num
                if next_dir_level == dir_level:
                    line_num = next_start_line_num
                    continue
                else:
                    return categories, next_dir_level, next_start_line_num
            if tab_num < dir_level:
                #print('sfs  parent category ', category_name)
                return categories, tab_num, line_num

        if re.match('^\s*\-\s+', line): # if current line corresponding to a post name
            tab, post_name  = re.findall(r'^(\s*)\-\s+(.*)', line)[0]
            tab_num = len(tab) / 2 - 1
            #print 'post_name ', line, ' current dir_level ', dir_level
            if tab_num == dir_level:
                category['posts'].append(post_name)
            if tab_num == -1:
                #print 'parent is global'
                global_category['posts'].append(post_name) 
            if tab_num < dir_level and tab_num > -1:
                return categories, tab_num, line_num
        line_num += 1
    return categories, 0, line_num + 1

def print_directory(category, dir_level):
    tab_num = 2 * dir_level + 2
    if 'categories' in category:
        for sub_category in category['categories']:
            for i in range(0, tab_num):
                print ' ',
            print '+ ', sub_category['name']
            print_directory(sub_category, dir_level + 1)
    
    if dir_level == -1:
        for post in category['posts']:
            print '- ' + post
    else:
        for post in category['posts']:
            for i in range(0, tab_num):
                print ' ',
            print '- ' + post
with open('test') as fp:
    lines  = fp.readlines()
    global_category['categories'] = get_directory(0, 0)[0]
    #print global_category
    print_directory(global_category, -1)
    
 
