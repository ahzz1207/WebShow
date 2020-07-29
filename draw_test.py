import json
import os
from requests_toolbelt import MultipartEncoder
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from sanic import Sanic, response
import jinja2
from jinja2 import Environment, PackageLoader, select_autoescape

app = Sanic(__name__)
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader('/Users/zhuangzehuang/Downloads/web_app/templates')
)

app.static('/static', './static')

upload_dir = "/Users/zhuangzehuang/Downloads/web_app/upload"
root_path = "/Users/zhuangzehuang/Downloads/web_app/static/"
static_path = "/static/draw"

keys_map = {}


def clear_map():
    global keys_map
    keys_map = {}


def template(tpl, **kwargs):
    template = env.get_template(tpl)
    return response.html(template.render(kwargs))


def highlight(text, h5_path):
    new_h5 = []
    file_name = h5_path.split(os.path.sep)[-1]
    with open(h5_path, 'r', encoding='utf-8') as f:
        for l in f.readlines():
            if text in l:
                print(l)
                l = l.replace(text, "<mark>" + text + "</mark>")
            new_h5.append(l)
    h5_path = os.path.join(root_path + "draw" + file_name)
    open(h5_path, "w").writelines(new_h5)
    return file_name


def upload(request, saved_path):
    file = request.files.get('file')
    upload_path = os.path.join(saved_path, file.name)
    with open(upload_path, 'wb') as f:
        f.write(file.body)
    f.close()
    return file.name.replace(".pdf", "")


def draw(file_abs_path, xy_):
    image = Image.open(file_abs_path)
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

    base_path = "/Users/zhuangzehuang/Downloads/web_app/static/draw"
    draw_abs_path = os.path.join(base_path, file_name)
    image.save(draw_abs_path)


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
        # return response.redirect(app.url_for('num', user_id=user_id))

        # return template('choose.html')


@app.route('/show/<file>', methods=['GET', 'POST'])
async def show(request, file):
    dir_path = os.path.join(root_path, file)
    # test_html = os.path.join(app.config['HTML_FOLDER'], 'train.html')
    if request.method == 'POST':
        print(request.form.keys())
        if 'restart' in request.form.keys():
            return response.redirect(app.url_for('homepage'))
        elif 'upload' in request.form.keys():
            return response.redirect(app.url_for('upload_page'))
        elif 'show_text' in request.form.keys():
            pics = []
            key = request.form.get('show_text')
            entities = keys_map[key]

            for e in entities:
                pic_names = e[0][0]
                poses = e[0][1]

                # for i in range(len(pic_names)):
                #     # 首先生成图片的绝对路径
                #     # i 只会是0或1， 对应pos里的第一张图或第二张图的位置
                #     pic_abs_path = os.path.join(dir_path, pic_names[i])
                #     xy_ = []
                #     for pos in poses:
                #         xy_.append(pos[i])
                #     draw(pic_abs_path, xy_)  # 以/static/draw/pic_name存储,
                #     draw_path = os.path.join(static_path, pic_names[i])
                #     if draw_path not in pics:
                #         pics.append(draw_path)
                h5_names = e[0][0]
                for i in range(len(pic_names)):
                    # 首先生成h5_path的绝对路径
                    # i 只会是0或1， 对应第一张图或第二张图
                    h5_abs_path = os.path.join(dir_path, h5_names[i])


            pic_paths = [os.path.join(static_path, pic_name.split(os.path.sep)[-1]) for pic_name in pics]
            print(pic_paths)
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
        file_json = json.load(open(json_path, "r"))

        # 得到一个list， 每个元素为一个甲方或乙方
        for key in ['合同编号', 'ORG_甲方', 'ORG_乙方', '合同金额', '合同签署日期', '合同款项支付日期', '标的']:
            if key in file_json.keys():
                keys_map[key] = []

                # 遍历该key的list， 其中每个元素是个map，对应该甲方/乙方的图片
                for e in file_json[key]:
                    # 遍历该甲方的所有图片数据
                    pic_names = e["picture_name"]  # list
                    text = e["text"]  # list
                    poses = e["pos"]  # list

                    if len(pic_names) > 1:
                        pic = file + "页码" + pic_names[0].replace(".jpg", "") + "-页码" +pic_names[1].replace(".jpg", "")
                    else:
                        pic = file + "页码" + pic_names[0].replace(".jpg", "")

                    keys_map[key].append(([pic_names, poses], text, pic))
        print(keys_map)

        return template('runtime.html', keys_map=keys_map,
                        pics=[], res_button="True")


@app.route('/', methods=['GET', 'POST'])
async def homepage(request):
    # test_html = os.path.join(app.config['HTML_FOLDER'], 'train.html')
    if request.method == 'POST':
        if 'upload' in request.form.keys():
            return response.redirect(app.url_for('upload_page'))

        clear_map()

        file = request.form['file'][0]

        return response.redirect(app.url_for('show', file=file))

    if request.method == 'GET':
        clear_map()
        # 遍历根目录下的所有子目录（对应文件）
        dir_list = os.listdir(root_path)
        dir_list.remove("draw")
        dir_list.remove(".DS_Store")
        print(dir_list)
        return template('runtime.html', files=dir_list, keys_map={})




if __name__ == '__main__':
    host_ip = '127.0.0.1'
    # host_ip = '0.0.0.0'
    # logging.getLogger('logger').info('WSGI Server running on: {}:{}'.format(host_ip, port_num))
    # print('PID:', os.getpid())
    app.run(host_ip=host_ip, port=5555)

