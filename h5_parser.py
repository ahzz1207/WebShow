import json
import os
from PIL import Image, ImageDraw
from sanic import Sanic, response
import jinja2
from bs4 import BeautifulSoup
import re

app = Sanic(__name__)
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader('/Users/zhuangzehuang/Downloads/web_app/templates')
)

app.static('/static', './static')

upload_dir = "/Users/zhuangzehuang/Downloads/web_app/upload"
root_path = "/Users/zhuangzehuang/Downloads/web_app/static/"
static_path = "/static/draw"

keys_map = {}

keys_map_h5 = {}


def clear_map():
    global keys_map
    keys_map = {}


def clear_map_h5():
    global keys_map_h5
    keys_map_h5 = {}


def edit(str1, str2):
    matrix = [[i + j for j in range(len(str2) + 1)] for i in range(len(str1) + 1)]

    for i in range(1, len(str1) + 1):
        for j in range(1, len(str2) + 1):
            if str1[i - 1] == str2[j - 1]:
                d = 0
            else:
                d = 1
            matrix[i][j] = min(matrix[i - 1][j] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j - 1] + d)

    return matrix[len(str1)][len(str2)]


def inserts(str, left, right):
    temp = list(str)
    for i in range(len(temp)):
        if temp[i] == left:
            for j in range(i + 1, len(temp)):
                if temp[j] == right:
                    temp.insert(i, "<br/>")
                    return ''.join(temp)
                elif temp[j] in ['<', '>', 'm', 'a', 'r', 'k']:
                    continue
                else:
                    break
        else:
            continue
    return str


def draw(file_abs_path, xy_):
    image = Image.open(file_abs_path)
    if not file_abs_path:
        return
    for xy in xy_:
        x1, y1, x2, y2 = int(xy[0]), int(xy[1]), int(xy[4]), int(xy[5])
        print(x1, y1, x2, y2)
        x_min = min(x1, x2)
        x_abs = abs(x1 - x2)
        y_min = min(y1, y2)
        y_abs = abs(y1 - y2)

        draw = ImageDraw.Draw(image)
        # TODO
        # 会不会有路径分隔符的错误
        file_name = file_abs_path.split(os.path.sep)[-1]
        print(file_name)
        for i in range(5):
            for x in range(x_abs):
                draw.point((x_min + x, y1 + i), fill=(255, 0, 0))
                draw.point((x_min + x, y2 + i), fill=(255, 0, 0))
            for y in range(y_abs):
                draw.point((x1 + i, y_min + y), fill=(255, 0, 0))
                draw.point((x2 + i, y_min + y), fill=(255, 0, 0))

    base_path = os.path.join(root_path, "draw")
    draw_abs_path = os.path.join(base_path, file_name)
    image.save(draw_abs_path)


def template(tpl, **kwargs):
    template = env.get_template(tpl)
    return response.html(template.render(kwargs))


def highlight2(h5_path, text_, xy_):
    file_name = h5_path.split(os.path.sep)[-1]

    h5 = open(h5_path, 'r', encoding='utf-8').readlines()
    for ti, xy in enumerate(xy_):
        top = xy[0]
        left = xy[1]
        text = text_[ti]
        match = """<div style="top:""" + top + ".000000px" + "; left:" + left + ".000000px" + """; position:absolute;">"""
        index = 0
        while index < len(h5):
            if h5[index] == match:
                # 加mark
                index += 1
                temp = h5[index]
                if temp.find("<br>") >= 0:
                    temps = temp.split('<br>')
                    for i in range(len(temps)):
                        if temps[i].find(text) >= 0:
                            temps[i] = temps[i].replace(text, "<mark>" + text + "</mark>")
                    temp = '<br>'.join(temps)
                    h5[index] = temp
                else:
                    h5[index] = temp.replace(text, "<mark>" + text + "</mark>")
            index += 1
    file_path = os.path.join(root_path, "draw", file_name)

    open(file_path, 'w', encoding="utf-8", ).writelines(h5)
    return file_path


def highlight(h5_path, text, h5_pos):
    file_name = h5_path.split(os.path.sep)[-1]
    soup = BeautifulSoup(open(h5_path, 'r'), "html.parser")
    for index, xy_ in enumerate(h5_pos):
        if len(xy_) == 5:
            # 画表格
            biao = xy_[0]
            sty = """background-color:yellow"""
            tables = soup.find_all("table")
            # for x in range(xy_[1], xy_[2] + 1):
            #     for y in range(xy_[3], xy_[4] + 1):
            x, y = xy_[1], xy_[3]
            print(f"target {x, y}")
            row = 1
            span = 0
            temp_row = 0
            table = tables[biao]
            for tr in table.find_all("tr"):
                col = 1

                for td in tr.find_all('td'):
                    # 修正偏移量
                    # if 'rowspan' in td.attrs and 'colspan' not in td.attrs:
                    #     temp_row = int(td.attrs['rowspan'])
                    #     if row < x < temp_row + row:
                    #         y -= 1
                    # elif 'rowspan' not in td.attrs and 'colspan' in td.attrs:
                    #     temp_col = int(td.attrs['colspan'])
                    #     if x == row:
                    #         y -= (temp_col - 1)
                    # elif 'rowspan' in td.attrs and 'colspan' in td.attrs:
                    #     temp_row = int(td.attrs['rowspan'])
                    #     temp_col = int(td.attrs['colspan'])
                    #     if row <= x < temp_row + row:
                    #         y -= (temp_col - 1)

                    # 对偏移量进行计算
                    rowspan = int(td.attrs['rowspan']) if 'rowspan' in td.attrs else 1
                    colspan = int(td.attrs['colspan']) if 'colspan' in td.attrs else 1
                    if x == row and col < y:
                        y -= (colspan - 1)
                    elif row < x < row + rowspan and col <= y:
                        y -= colspan

                    print(f"当前行列{row, col}, real_target {x, y}")
                    if row == x and col == y:
                        td['style'] = sty
                        print(x, y)
                    col += 1
                row += 1

                # for tr in table.find_all("tr"):
                #     clo = 1
                #     td = tr.find('td')
                # if 'rowspan' in td.attrs:
                #     temp_row = row
                #     span = int(td['rowspan']) + temp_row - 1
                # if 'colspan' in td.attrs:
                #     temp_clo = clo
                #     span_c = int(td['colspan'])
                # for td in tr.find_all("td"):
                # if span >= row > temp_row:
                #     if row == x and (clo + 1) == y:
                #         td['style'] = sty
                #
                # else:
                #     if row == x and clo == y:
                #         td['style'] = sty
                # clo += 1

                # if span == row:
                #     span = 0
                #     temp_row = 0
                # row += 1

        elif len(xy_) == 9:
            print(xy_)
            # 高亮文字
            left = str(min(int(xy_[0]), int(xy_[2]), int(xy_[4]), int(xy_[6])))
            top = str(min(int(xy_[1]), int(xy_[3]), int(xy_[5]), int(xy_[7])))
            text_index = int(xy_[8])
            temp_text = text[text_index]
            for s in soup.find_all():
                if "style" in s.attrs:
                    m = "top:" + top + ".000000px; left:" + left + ".000000px;"
                    #
                    if s['style'].find(m) >= 0:
                        # 替换<单位>
                        reg = re.compile("(<.*?>)")
                        if re.findall(reg, temp_text):
                            temp_text = re.sub(reg, "", temp_text)

                        # 进入高亮程序
                        s = s.div
                        # 如果文本能匹配上
                        if s.text.find(temp_text) >= 0:
                            # 对带有换行的特殊处理
                            if s.br:
                                print(s)
                                strs = list(s)
                                left = strs[0][-1]
                                right = strs[-1][0]
                                temp = s.text
                                s.string = temp.replace(temp_text, "<mark>" + temp_text + "</mark>")
                                s.string = inserts(s.text, left, right)
                            # 否则普通替换即可
                            else:
                                print(s, temp_text)
                                temp = s.text
                                s.string = temp.replace(temp_text, "<mark>" + temp_text + "</mark>")
                            print(s)

                        else:
                            s['style'] += ";background-color:yellow;"

    # 对转义进行处理
    h5_path = os.path.join(root_path, "draw", file_name)
    with open(h5_path, "wb")as f:
        raw = soup.prettify(encoding="utf-8")
        raw = raw.replace(b'&lt;', b'<')
        raw = raw.replace(b'&gt;', b'>')
        f.write(raw)
    f.close()

    return file_name, h5_path


def upload(request, saved_path):
    file = request.files.get('file')
    upload_path = os.path.join(saved_path, file.name)
    with open(upload_path, 'wb') as f:
        f.write(file.body)
    f.close()
    return file.name.replace(".pdf", "")


@app.route('/upload', methods=['GET', 'POST'])
async def upload_page(request):
    if request.method == 'GET':
        return template('upload.html')
    if request.method == 'POST':
        if 'analysis' in request.form:
            file_name = upload(request, upload_dir)
            return response.redirect(app.url_for('show', file=file_name))
        else:
            return response.redirect(app.url_for('homepage'))


@app.route('/show/<file>', methods=['GET', 'POST'])
async def show(request, file):
    dir_path = os.path.join(root_path, file)
    if request.method == 'POST':
        print(request.form.keys())
        if 'restart' in request.form.keys():
            return response.redirect(app.url_for('homepage'))
        elif 'upload' in request.form.keys():
            return response.redirect(app.url_for('upload_page'))
        elif 'all' in request.form.keys():
            all_pics = []

            files = os.listdir(root_path + file)
            for f in sorted(files):
                if f.split('.')[-1] == 'jpg':
                    all_pics.append(f)
            all_pics = [os.path.join('/static', file, pic) for pic in all_pics]
            return template('runtime.html', keys_map=keys_map,
                            pics=all_pics, res_button="True")

        elif 'show_text' in request.form.keys():
            pics = []
            key = request.form.get('show_text')
            if key != "支付":
                entities = keys_map[key]

                for e in entities:
                    pic_names = e[0][0]
                    poses = e[0][1]

                    for i in range(len(pic_names)):
                        # 首先生成图片的绝对路径
                        # i 只会是0或1， 对应pos里的第一张图或第二张图的位置
                        pic_abs_path = os.path.join(dir_path, pic_names[i])
                        xy_ = []
                        for pos in poses:
                            if len(pos) > i:
                                xy_.append(pos[i])
                        draw(pic_abs_path, xy_)  # 以/static/draw/pic_name存储,
                        draw_path = os.path.join(static_path, pic_names[i])
                        if draw_path not in pics:
                            pics.append(draw_path)
            else:

            pic_paths = [os.path.join(static_path, pic_name.split(os.path.sep)[-1]) for pic_name in pics]
            print(f"保存的图片位于{pic_paths}")
            return template('runtime.html', keys_map=keys_map,
                            pics=pic_paths, res_button="True")
        else:
            return response.redirect(app.url_for('homepage'))

    if request.method == 'GET':
        # 对应pdf的图片文件夹
        clear_map()
        dir_path = os.path.join(root_path, file)
        json_path = ""
        # 扫描该pdf文件夹下的所有文件
        picture_names = []
        file_names = os.listdir(dir_path)
        for file_name in file_names:
            if file_name == "result.json":
                # 读取该文件夹下的json文件，形成甲方乙方的map
                json_path = os.path.join(dir_path, file_name)
            elif file_name.split('.')[-1] == 'jpg':
                picture_names.append(file_name)
        # {key:[[[text, pos], [text, pos]]]}
        print(json_path)
        file_json = json.load(open(json_path, "r", encoding="utf-8"))

        # 得到一个list， 每个元素为一个甲方或乙方
        # for key in ['contract_number', 'org_A', 'org_B', 'contract_money', 'date_sign', 'contract_payment_date',
        #             'contract_tgt']:
        for key in ['甲方', '乙方', '合同编号', '签约日期', '合同金额', '合同支付日期', '合同标的', '合同账期', '支付方式']:
            if key in file_json.keys():
                keys_map[key] = []

                # 遍历该key的list， 其中每个元素是个map，对应该甲方/乙方的图片
                for e in file_json[key]:
                    # 遍历该甲方的所有图片数据
                    pic_names = e["picture_name"]  # list
                    text = e["text"]  # list
                    poses = e["pos"]  # list

                    if len(pic_names) > 1:
                        pic = file + "  页码" + pic_names[0].replace(".jpg", "") + "-页码" + pic_names[1].replace(".jpg",
                                                                                                              "")
                    else:
                        pic = file + "  页码" + pic_names[0].replace(".jpg", "")

                    keys_map[key].append(([pic_names, poses], text, pic))
        print(keys_map)

        return template('runtime.html', keys_map=keys_map,
                        pics=[], res_button="True")


@app.route('/show_h5/<file>', methods=['GET', 'POST'])
async def show_h5(request, file):
    dir_path = os.path.join(root_path, file)
    if request.method == 'POST':
        print(request.form.keys())
        if 'restart' in request.form.keys():
            return response.redirect(app.url_for('homepage_h5'))
        elif 'upload' in request.form.keys():
            return response.redirect(app.url_for('upload_page'))
        elif 'all' in request.form.keys():
            all_pics = []
            files = os.listdir(root_path + file)
            for f in sorted(files):
                if f.split('.')[-1] == 'html':
                    all_pics.append(f)
            all_pics = [os.path.join('/static', file, pic) for pic in all_pics]
            return template('runtime.html', keys_map=keys_map,
                            pics=all_pics, res_button="True")
        elif 'show_text' in request.form.keys():
            h5 = []
            key = request.form.get('show_text')
            entities = keys_map[key]

            all_pics = []

            for e in entities:
                all_pics += e[1]
            for e in entities:
                text = e[1]
                h5_names = e[0]
                table_pos = e[2]
                for i in range(len(h5_names)):
                    # 首先生成h5_path的绝对路径
                    # i 只会是0或1， 对应第一张图或第二张图
                    h5_abs_path = os.path.join(dir_path, h5_names[i])
                    table_pos_ = []
                    for pos in table_pos:
                        if len(pos) > i:
                            table_pos_.append(pos[i])
                    h5_name, h5_draw_path = highlight(h5_abs_path, text, table_pos_)
                    if h5_name not in h5:
                        h5.append(h5_name)

            h5_paths = [os.path.join(static_path, h5_name) for h5_name in h5]
            print(f"保存的h5文件位于：{h5_paths}")
            return template('runtime.html', keys_map=keys_map,
                            pics=h5_paths, res_button="True")
        else:
            return response.redirect(app.url_for('homepage_h5'))

    if request.method == 'GET':
        # 解析对应文件夹下的所有文件（result.json）
        clear_map()
        dir_path = os.path.join(root_path, file)
        json_path = ""
        # 扫描该pdf文件夹下的所有文件
        picture_names = []
        h5_names = []
        file_names = os.listdir(dir_path)
        for file_name in file_names:
            if file_name == "result.json":
                # 读取该文件夹下的json文件，形成甲方乙方的map
                json_path = os.path.join(dir_path, file_name)
            elif file_name.split('.')[-1] == 'html':
                h5_names.append(file_name)
            elif file_name.split('.')[-1] == 'jpg':
                picture_names.append(file_name)
        # {key:[[[text, pos], [text, pos]]]}
        print(json_path)
        file_json = json.load(open(json_path, "r", encoding="utf-8"))

        # 得到一个list， 每个元素为一个甲方或乙方
        # for key in ['contract_number', 'org_A', 'org_B', 'contract_money', 'date_sign', 'contract_payment_date', 'contract_tgt']:
        for key in ['甲方', '乙方', '合同编号', '签约日期', '合同金额', '合同支付日期', '合同标的', '合同账期', '支付方式']:
            if key in file_json.keys():
                keys_map[key] = []

                # 遍历该key的list， 其中每个元素是个map，对应该甲方/乙方的图片
                for e in file_json[key]:
                    # 遍历该甲方的所有图片数据
                    pic_names = e["picture_name"]  # list
                    h5_names = []
                    for p in pic_names:
                        if p.split(".")[-1] == "jpg":
                            h5_names.append(p.split(".")[0] + ".html")
                    h5_pos = e['h5_pos']
                    text = e["text"]  # list
                    h5_desc = file + "  页码" + h5_names[0].replace(".html", "")

                    keys_map[key].append((h5_names, text, h5_desc, h5_pos))
        print(keys_map)

        return template('runtime.html', keys_map=keys_map,
                        pics=[], res_button="True")


@app.route('/', methods=['GET', 'POST'])
async def homepage(request):
    # test_html = os.path.join(app.config['HTML_FOLDER'], 'train.html')
    if request.method == 'POST':
        # 进入上传页面
        if 'upload' in request.form.keys():
            return response.redirect(app.url_for('upload_page'))

        # 否则是清理缓存，重定向到选择的文件目录下
        clear_map()

        file = request.form['file'][0]

        return response.redirect(app.url_for('show', file=file))

    if request.method == 'GET':
        clear_map()
        # 遍历根目录下的所有子目录（对应文件）
        dir_list = os.listdir(root_path)
        if "draw" in dir_list:
            dir_list.remove("draw")
        # 如果是mac系统
        if ".DS_Store" in dir_list:
            dir_list.remove(".DS_Store")
        return template('runtime.html', files=dir_list, keys_map={}, all="false")


@app.route('/h5', methods=['GET', 'POST'])
async def homepage_h5(request):
    # test_html = os.path.join(app.config['HTML_FOLDER'], 'train.html')
    if request.method == 'POST':
        # 进入上传页面
        if 'upload' in request.form.keys():
            return response.redirect(app.url_for('upload_page'))

        # 否则是清理缓存，重定向到选择的文件目录下
        clear_map()

        file = request.form['file'][0]

        return response.redirect(app.url_for('show_h5', file=file))

    if request.method == 'GET':
        clear_map()
        # 遍历根目录下的所有子目录（对应文件）
        dir_list = os.listdir(root_path)
        if "draw" in dir_list:
            dir_list.remove("draw")
        # 如果是mac系统
        if ".DS_Store" in dir_list:
            dir_list.remove(".DS_Store")
        return template('runtime.html', files=dir_list, keys_map={}, all="false")


if __name__ == '__main__':
    host_ip = '127.0.0.1'
    app.run(host_ip=host_ip, port=5555)
