import json
import os
from PIL import Image, ImageDraw
from sanic import Sanic, response
import jinja2
from bs4 import BeautifulSoup
import re

template_path = '/Users/zhuangzehuang/Downloads/web_app/templates'
app = Sanic(__name__)
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_path)
)

app.static('/static', './static')

upload_dir = "/Users/zhuangzehuang/Downloads/web_app/upload"
root_path = "/Users/zhuangzehuang/Downloads/web_app/static/"
static_path = "/static/draw"

keys_map = {}

keys_map_h5 = {}

contract_num = {'c': 1}


def clear_contract_num():
    global contract_num
    contract_num['c'] = 1


def clear_map():
    global keys_map
    keys_map = {}


def clear_map_h5():
    global keys_map_h5
    keys_map_h5 = {}


def clear_all():
    clear_contract_num()
    clear_map()
    clear_map_h5()


def close_tr(h5_path, saved_path):
    line = open(h5_path, "r", encoding="utf-8").readlines()
    i = 0
    length = len(line)
    while i < length:
        # 查找该tr是否正常闭合
        if line[i] == "</tr>\n":
            j = i + 1
            while j < length:
                # 若缺少tr 添加
                if line[j] == "</tr>\n":
                    print(i)
                    line.insert(i + 1, "<tr>\n")
                    # 继续遍历
                    length += 1
                    i += 1
                    break
                # 正常闭合，继续遍历
                elif line[j] == "<tr>\n":
                    i += 1
                    break
                else:
                    j += 1
            i += 1
        else:
            i += 1
    # h5_path = os.path.join(static_path, 'draw', h5_name)
    open(saved_path, "w", encoding="utf-8").writelines(line)
    print(f"write done {saved_path}")


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


def draw(text, poses):

    for i, text in enumerate(text):
        xy_ = poses[i]
        for xy in xy_:
            x1, y1, x2, y2 = int(xy[0]), int(xy[1]), int(xy[4]), int(xy[5])
            print(x1, y1, x2, y2)
            x_min = min(x1, x2)
            x_abs = abs(x1 - x2)
            y_min = min(y1, y2)
            y_abs = abs(y1 - y2)
            file_abs_path = os.path.join(root_path, 'draw', 'p' +str(xy[8]) + '.jpg')

            image = Image.open(file_abs_path)
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


def highlight(text, h5_pos):

    for index, poses in enumerate(h5_pos):
        temp_text = text[index]
        for xy_ in poses:
            if len(xy_) == 6:
                h5_name = 'p' + str(xy_[5]) + '.html'
                h5_path = os.path.join(root_path, "draw", h5_name)
            elif len(xy_) == 9:
                h5_name = 'p' + str(xy_[8]) + '.html'
                h5_path = os.path.join(root_path, "draw", h5_name)

            soup = BeautifulSoup(open(h5_path, 'r'), "html.parser")
            if len(xy_) == 6:
                # 画表格
                biao = xy_[0]
                sty = """background-color:yellow"""
                tables = soup.find_all("table")
                x, y = xy_[1], xy_[3]
                print(f"target {x, y}")
                row = 1

                table = tables[biao]
                trs = table.find_all("tr")
                for tr in trs:
                    col = 1

                    for td in tr.find_all('td'):
                        # 对偏移量进行计算
                        rowspan = int(td.attrs['rowspan']) if 'rowspan' in td.attrs else 1
                        colspan = int(td.attrs['colspan']) if 'colspan' in td.attrs else 1

                        if row == x and col == y:
                            td['style'] = sty
                            print(x, y)
                            break

                        if x == row and col < y:
                            y -= (colspan-1)
                        elif row < x < row + rowspan and col <= y:
                            y -= colspan

                        print(f"当前行列{row, col}, real_target {x, y}")

                        col += 1
                    else:
                        row += 1
                        continue
                    break

            elif len(xy_) == 9:
                print(xy_)
                # 高亮文字
                left = str(min(int(xy_[0]), int(xy_[2]), int(xy_[4]), int(xy_[6])))
                top = str(min(int(xy_[1]), int(xy_[3]), int(xy_[5]), int(xy_[7])))

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
            with open(h5_path, "wb")as f:
                raw = soup.prettify(encoding="utf-8")
                raw = raw.replace(b'&lt;', b'<')
                raw = raw.replace(b'&gt;', b'>')
                f.write(raw)
            f.close()


def upload(request, saved_path):
    file = request.files.get('file')
    upload_path = os.path.join(saved_path, file.name)
    with open(upload_path, 'wb') as f:
        f.write(file.body)
    f.close()
    return file.name.replace(".pdf", "")


@app.route('/upload', methods=['GET', 'POST'])
def upload_page(request):
    if request.method == 'GET':
        return template('upload.html')
    if request.method == 'POST':
        if 'analysis' in request.form:
            file_name = upload(request, upload_dir)
            return response.redirect(app.url_for('show', file=file_name))
        else:
            return response.redirect(app.url_for('homepage'))


@app.route('/show/<file>', methods=['GET', 'POST'])
def show(request, file):
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
            return template('runtime.html', keys_map=keys_map, file="《"+file+"》",
                            pics=all_pics, res_button="True", contract_num=contract_num['c'])

        elif 'show_text' in request.form.keys():
            key = request.form.get('show_text')
            if key:
                entities = keys_map[key]

                # 把所有要画的图片先保存到draw文件夹
                all_pics = set()
                for e in entities:
                    for f in e[0]:
                        all_pics.add(f)
                print(all_pics)
                all_pics = list(all_pics)
                # 文件夹下路径
                all_pics_path = [os.path.join(dir_path, i) for i in all_pics]
                # 保存到资源地址的绝对路径
                saved_path = [os.path.join(root_path, 'draw', i) for i in all_pics]
                # 资源地址的想对路径
                draw_path = [os.path.join(static_path, i) for i in all_pics]

                for i, pics_path in enumerate(all_pics_path):
                    image = Image.open(pics_path)
                    image.save(saved_path[i])

                # 开始画图
                for e in entities:
                    pic_names = e[0]
                    text = e[1][1]
                    poses = e[1][0]

                    # 一次画一个实体
                    draw(text, poses)
            print(f"保存的图片位于{draw_path}")
            return template('runtime.html', keys_map=keys_map,
                            pics=sorted(draw_path), res_button="True", contract_num=contract_num['c'], file="《"+file+"》")
        else:
            return response.redirect(app.url_for('homepage'))

    if request.method == 'GET':
        # 对应pdf的图片文件夹
        clear_all()
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
        contract_num['c'] = file_json['contract_count'] if 'contract_count' in file_json else 1
        for key in ['甲方', '乙方', '合同编号', '签约日期', '合同金额', '合同支付日期', '合同标的', '合同账期', '支付方式']:
            if key in file_json.keys():
                keys_map[key] = []

                # 遍历该key的list， 其中每个元素是个map，对应该甲方/乙方的图片
                for e in file_json[key]:
                    # 遍历该甲方的所有图片数据
                    pic_names = e["picture_name"]  # list
                    text = e["text"]  # list
                    poses = e["pos"]  # list
                    show_text = []
                    for t in text:
                        reg = re.compile("(<.*?>)")
                        match = re.findall(reg, t)

                        if match:
                            t = re.sub(reg, "", t)
                            t += match[0].split('<')[-1].split('>')[0]
                        show_text.append(t)

                    for p in pic_names:
                        pic_desc = " 页码- " + p.replace(".html", "")

                    keys_map[key].append((pic_names, (poses, text), pic_desc, show_text))
        print(keys_map)

        return template('runtime.html', keys_map=keys_map, contract_num=contract_num['c'],
                        pics=[], res_button="True", file="《"+file+"》")


@app.route('/show_h5/<file>', methods=['GET', 'POST'])
def show_h5(request, file):
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
            return template('runtime.html', keys_map=keys_map, contract_num=contract_num['c'],
                            pics=all_pics, res_button="True", file="《"+file+"》")
        elif 'show_text' in request.form.keys():
            key = request.form.get('show_text')
            entities = keys_map[key]

            all_h5 = set()
            for e in entities:
                for f in e[0]:
                    all_h5.add(f)
            print(all_h5)
            all_h5 = list(all_h5)
            # 文件夹下路径
            all_h5_path = [os.path.join(dir_path, i) for i in all_h5]
            # 保存到资源地址的绝对路径
            h5_saved_path = [os.path.join(root_path, 'draw', i.split('.')[0]+'.html') for i in all_h5]
            # 资源地址的想对路径
            h5_draw_path = [os.path.join(static_path, i) for i in all_h5]

            for i, h5_path in enumerate(all_h5_path):
                close_tr(h5_path, h5_saved_path[i])

            for e in entities:
                text = e[1][1]
                table_pos = e[1][0]
                highlight(text, table_pos)

            print(f"保存的h5文件位于：{h5_draw_path}")
            return template('runtime.html', keys_map=keys_map, file="《"+file+"》",
                            pics=sorted(h5_draw_path), res_button="True", contract_num=contract_num['c'])
        else:
            return response.redirect(app.url_for('homepage_h5'))

    if request.method == 'GET':
        # 解析对应文件夹下的所有文件（result.json）
        clear_all()
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
        contract_num['c'] = file_json['contract_count'] if 'contract_count' in file_json else 1
        # 得到一个list， 每个元素为一个甲方或乙方
        for key in ['甲方', '乙方', '合同编号', '签约日期', '合同金额', '合同支付日期', '合同标的', '合同账期', '支付方式']:
            if key in file_json.keys():
                keys_map[key] = []
                for e in file_json[key]:
                    # 遍历该甲方的所有图片数据
                    pic_names = e["picture_name"]  # list
                    h5_names = []
                    text = e["text"]  # list
                    h5_pos = e["h5_pos"]  # list
                    show_text = []
                    for p in pic_names:
                        if p.split(".")[-1] == "jpg":
                            h5_names.append(p.split(".")[0] + ".html")
                    for t in text:
                        reg = re.compile("(<.*?>)")
                        match = re.findall(reg, t)

                        if match:
                            t = re.sub(reg, "", t)
                            t += match[0].split('<')[-1].split('>')[0]
                        show_text.append(t)

                    for h in h5_names:
                        h5_desc = " 页码- " + h.replace(".html", "")
                    keys_map[key].append((h5_names, (h5_pos, text), h5_desc, show_text))
        print(keys_map)

        return template('runtime.html', keys_map=keys_map,
                        pics=[], res_button="True", contract_num=contract_num['c'], file="《"+file+"》")


@app.route('/', methods=['GET', 'POST'])
def homepage(request):
    if request.method == 'POST':
        # 进入上传页面
        if 'upload' in request.form.keys():
            return response.redirect(app.url_for('upload_page'))

        # 否则是清理缓存，重定向到选择的文件目录下
        clear_all()

        file = request.form['file'][0]

        return response.redirect(app.url_for('show', file=file))

    if request.method == 'GET':
        clear_all()
        # 遍历根目录下的所有子目录（对应文件）
        dir_list = os.listdir(root_path)
        if "draw" in dir_list:
            dir_list.remove("draw")
        # 如果是mac系统
        if ".DS_Store" in dir_list:
            dir_list.remove(".DS_Store")
        return template('runtime.html', files=dir_list, keys_map={}, all="false")


@app.route('/h5', methods=['GET', 'POST'])
def homepage_h5(request):
    # test_html = os.path.join(app.config['HTML_FOLDER'], 'train.html')
    if request.method == 'POST':
        # 进入上传页面
        if 'upload' in request.form.keys():
            return response.redirect(app.url_for('upload_page'))

        # 否则是清理缓存，重定向到选择的文件目录下
        clear_all()

        file = request.form['file'][0]

        return response.redirect(app.url_for('show_h5', file=file))

    if request.method == 'GET':
        clear_all()
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
