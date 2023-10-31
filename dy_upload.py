import json
import os
import re
import subprocess
import time
import requests
import xmltodict
import yaml
import argparse
import logging
import sys
from PIL import Image
from ffmpy import FFmpeg
from playwright.sync_api import Playwright, sync_playwright

UPLOAD_SLEEP_SECOND = 60 * 2  # 2min
UPLOADED_VIDEO_FILE = "dy_uploaded_video.json"
CONFIG_FILE = "config.json"
COOKIE_FILE = "dy_cookie.json"
VERIFY = os.environ.get("verify", "1") == "1"
PROXY = {
    "https": os.environ.get("https_proxy", None)
}


def get_gist(_gid, token):
    """通过 gist id 获取已上传数据"""
    rsp = requests.get(
        "https://api.github.com/gists/" + _gid,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
        },
        verify=VERIFY,
    )
    if rsp.status_code == 404:
        raise Exception("gist id 错误")
    if rsp.status_code == 403 or rsp.status_code == 401:
        raise Exception("github TOKEN 错误")
    _data = rsp.json()
    uploaded_file = _data.get("files", {}).get(
        UPLOADED_VIDEO_FILE, {}).get("content", "{}")
    c = json.loads(_data["files"][CONFIG_FILE]["content"])
    t = json.loads(_data["files"][COOKIE_FILE]["content"])
    try:
        u = json.loads(uploaded_file)
        return c, t, u
    except Exception as e:
        logging.error(f"gist 格式错误，重新初始化:{e}")
    return c, t, {}


def update_gist(_gid, token, file, data):
    rsp = requests.post(
        "https://api.github.com/gists/" + _gid,
        json={
            "description": "y2b暂存数据",
            "files": {
                file: {
                    "content": json.dumps(data, indent="  ", ensure_ascii=False)
                },
            }
        },
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
        },
        verify=VERIFY,
    )
    if rsp.status_code == 404:
        raise Exception("gist id 错误")
    if rsp.status_code == 422:
        raise Exception("github TOKEN 错误")


def get_file_size(filename):
    sz = os.path.getsize(filename)
    return int(sz/1024/1024)


def get_video_list(channel_id: str):
    print(channel_id)
    res = requests.get(
        "https://www.youtube.com/feeds/videos.xml?" + channel_id).text
    res = xmltodict.parse(res)
    ret = []
    for elem in res.get("feed", {}).get("entry", []):
        ret.append({
            "vid": elem.get("yt:videoId"),
            "title": elem.get("title"),
            "origin": "https://www.youtube.com/watch?v=" + elem["yt:videoId"],
            "cover_url": elem["media:group"]["media:thumbnail"]["@url"],
            # "desc": elem["media:group"]["media:description"],
        })
    return ret


def select_not_uploaded(video_list: list, _uploaded: dict):
    ret = []
    for i in video_list:
        if _uploaded.get(i["detail"]["vid"]) is not None:
            logging.debug(f'vid:{i["detail"]["vid"]} 已被上传')
            continue
        logging.debug(f'vid:{i["detail"]["vid"]} 待上传')
        ret.append(i)
    return ret


def get_all_video(_config):
    ret = []
    for i in _config:
        res = get_video_list(i["channel_id"])
        for j in res:
            ret.append({
                "detail": j,
                "config": i
            })
    return ret


def download_video(url, out, format):
    try:
        msg = subprocess.check_output(
            ["yt-dlp", url, "-f", format, "-o", out], stderr=subprocess.STDOUT)
        logging.debug(msg[-512:])
        logging.info(f"视频下载完毕，大小：{get_file_size(out)} MB")
        return True
    except subprocess.CalledProcessError as e:
        out = e.output.decode("utf8")
        if "This live event will begin in" in out:
            logging.info("直播预告，跳过")
            return False
        if "Requested format is not available" in out:
            logging.debug("视频无此类型：" + format)
            return False
        if "This video requires payment to watch" in out:
            logging.info("付费视频，跳过")
            return False
        logging.error("未知错误:" + out)
        return False
        raise e

def copy_file(source_file, target_file):
    # 打开原文件和目标文件
    with open(source_file, 'rb') as sf, open(target_file, 'wb') as tf:
        # 读取原文件的内容
        content = sf.read()
        # 将读取到的内容写入目标文件
        tf.write(content) 
def download_cover(url, out):
    url=url.replace("hqdefault.jpg","maxresdefault.jpg")
    #maxresdefault.jpg
    resp = requests.get(url, verify=VERIFY)
    logging.info("picpic")
    res=resp.content 
    with open(out, "wb") as tmp:
        tmp.write(res)

def upload(playwright: Playwright,video,cover,config,detail,cookie) -> None: 
    
    logging.info("开始")
    title = detail['title']
    if len(title) > 80:
        title = title[:80]
    browser =  playwright.chromium.launch(headless=True)
    #browser =  playwright.chromium.launch(headless=False)
    context =  browser.new_context(storage_state=cookie,viewport={'width': 1920, 'height': 1080},locale="zh-CN",record_video_dir="./screenshot/",
                                   record_video_size={"width": 1920, "height": 1080},
                                   user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')

    logging.info("授权位置权限")
    context.grant_permissions(['geolocation'], origin='https://creator.douyin.com')
    context.add_init_script(path='stealth.min.js')
    page =  context.new_page()
    try:
        # # 关闭Webdriver属性
        #js = """
        #        Object.defineProperties(navigator, {webdriver:{get:()=>undefined}});
        #        """
        #page.add_init_script(js)
        
        logging.info("打开上传页面")
        #page.goto("https://bot.sannysoft.com/")
       
        page.goto("https://creator.douyin.com/creator-micro/content/upload?enter_from=dou_web",timeout=50000)
        page.screenshot(path='./screenshot/example.png')
        page.locator('xpath=//*/div[@class="tab-item--33ZEJ active--2Abua"]').click(timeout=100000)
        logging.info("等待上传页面加载完成") 
        page.screenshot(path='./screenshot/example1.png') 
        logging.info("点击上传:"+video)
        page.locator(
            "span:has-text(\"点击上传 \")").set_input_files(video,timeout=1000000) 
        page.screenshot(path='./screenshot/example2.png')  
        page.wait_for_timeout(6000)
        page.on("dialog", lambda dialog: dialog.accept())
        try:
            page.get_by_role("button", name="确定").click()
            print("出现了《云草稿自动保存》的弹出《确定》按钮")
            page.get_by_role("button", name="取消").click()
            print("出现了《选择画布》的弹出《取消》按钮")
        except:
            print("没有找到《云草稿自动保存》《创建》的按钮")
            pass
        #print("点击发布")
        page.locator("div").filter(has_text=re.compile(r"^视频分类请选择视频内容分类$")).locator("svg").nth(1).click(timeout=1000000)
        page.screenshot(path='./screenshot/example3.png')
        page.get_by_text("教育校园").click(timeout=100000)
        page.wait_for_timeout(6000)
        page.get_by_text("语言").click(timeout=100000)
        page.get_by_text("英语").click(timeout=100000)
        page.wait_for_timeout(6000)
        page.get_by_text("语言情景剧").click(timeout=100000)
        page.get_by_text("请选择合集").click(timeout=100000)
        page.get_by_text(config['tags']).click(timeout=100000)
        logging.info(f"打印到这来了")
    
        #page.get_by_placeholder(text=re.compile(r".*标题，.*更多人.*")).fill(title,timeout=10000000)
        #page.get_by_placeholder("写一个合适的标题，会有更多人看到").fill(title,timeout=10000000)
        #page.locator(".zone-container").filter(text=re.compile(r".*标题，.*更多人.*")).fill(title)
        page.locator(".zone-container").fill(title)
        logging.info(cover)
        try:
            img = Image.open(cover)
            if img.width>672 and img.height >504: 
                page.locator("div").filter(has_text=re.compile(r"^选择封面$")).nth(2).click(timeout=1000000)
                page.get_by_text("上传封面").click(timeout=10000000)
                #page.get_by_text("点击上传 或直接将图片文件拖入此区域建议上传4:3(横)或3:4(竖)比例的高清图片，清晰美观的封面利于推荐").click(timeout=1000000)
                logging.info("上传"+cover)
                page.locator(".semi-upload-hidden-input").set_input_files(cover,timeout=100000)
                #page.get_by_role("button", name="完成").click(timeout=100000)
                page.locator(".semi-button-content").filter(has_text="完成")
                page.get_by_role("button", name="完成").click()
            img.close()
        except Exception as e:
            logging.info(e)
        page.on("dialog", lambda dialog: dialog.accept())
        time.sleep(5)
        try:
                page.get_by_text("我知道了").click()
        except:
            print("没有找到《我知道了》的按钮")
            pass
        print("点击发布")
    
        page.locator(
        'xpath=//*[@id="root"]//div/button[@class="button--1SZwR primary--1AMXd fixed--3rEwh"]').click(timeout=20000)
        page.wait_for_timeout(6000)
        #path=os.getcwd() + 
        context.storage_state(path=COOKIE_FILE)
    except Exception as e:
        logging.info(e)
        logging.info(page.content())
        raise e
    finally:
        context.close()
        browser.close()
    return {}




def process_one(detail, config, cookie):
    logging.info(f'开始：{detail["vid"]}')
    format = ["webm", "flv", "mp4"]
    v_ext = None
    video = None
    for ext in format:
        video = detail["vid"] + f".{ext}"
        if download_video(detail["origin"], video, f"{ext}"):
            v_ext = ext
            logging.info(f"使用格式：{ext}")
            break
    if v_ext is None:
        logging.error("无合适格式")
        return
    logging.info(f"如果视频文件小于5M,不搬运")
    if get_file_size(video) < 5:
        return
    #ff = FFmpeg()
    ff = FFmpeg(
        inputs={video: None, 'logo000.png': None},
        #右下角outputs={'./screenshot/output.mp4': '-filter_complex "overlay=main_w-overlay_w-10:main_h-overlay_h-10"'}
        outputs={'./video/output.mp4': '-filter_complex "overlay=main_w-overlay_w-10:10"'}
    )
    #ff.options("-i "+video+" -i logo00.png -filter_complex overlay= main_w-overlay_w:0 ./screenshot/output.mp4")
    print(ff.cmd)
    ff.run()
    video='./video/output.mp4'
    download_cover(detail["cover_url"], detail["vid"] + ".jpg")
    logging.info(f"打印到这来了")
    #ret = upload_video(video,detail["vid"] + ".jpg", config, detail)
    logging.info(f"打印到这来了")
    with sync_playwright() as playwright:
        #ret = upload(playwright, video,detail["vid"] + ".jpg", config, detail,cookie)
        try:
            ret = upload(playwright,video,detail["vid"] + ".jpg", config, detail,cookie)
        except Exception as e:
            logging.info(e)
            
    print("点击发布")
    if ret is None:
        return
    os.remove(video)
    os.remove(detail["vid"] + ".jpg")
    return {}


def upload_process(gist_id, token):
    config, cookie, uploaded = get_gist(gist_id, token)
    with open("cookies.json", "w", encoding="utf8") as tmp:
        tmp.write(json.dumps(cookie))
    need_to_process = get_all_video(config)
    need = select_not_uploaded(need_to_process, uploaded)
    for i in need:
        ret = process_one(i["detail"], i["config"], cookie)
        if ret is None:
            continue
        i["ret"] = ret
        uploaded[i["detail"]["vid"]] = i
        update_gist(gist_id, token, UPLOADED_VIDEO_FILE, uploaded)
        logging.info(
            f'gist file更新上传完成,vid:{i["detail"]["vid"]}')
        break
        logging.debug(f"防验证码，暂停 {UPLOAD_SLEEP_SECOND} 秒")
        time.sleep(UPLOAD_SLEEP_SECOND)
    with open("cookies.json", encoding="utf8") as tmp:
        data = tmp.read()
        update_gist(gist_id, token, COOKIE_FILE, json.loads(data))
        logging.info("gist cookie更新上传完成")
    os.remove("cookies.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("token", help="github api token", type=str)
    parser.add_argument("gistId", help="gist id", type=str)
    parser.add_argument("--logLevel", help="log level, default is info",
                        default="INFO", type=str, required=False)
    args = parser.parse_args()
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.getLevelName(args.logLevel),
        format='%(filename)s:%(lineno)d %(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
        datefmt="%H:%M:%S",
    )
    os.mkdir("screenshot")
    os.mkdir("video")
    upload_process(args.gistId, args.token)
        
    
