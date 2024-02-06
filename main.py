import requests as r
import json
import os
import re
import sentry_sdk
import random
import time
import yaml

def ReadConf(variable_name, default_value=None):
    # Try to get the variable from the environment
    env_value = os.environ.get(variable_name)

    if env_value is not None:
        config_data = yaml.load(env_value, Loader=yaml.FullLoader)
        return config_data

    # If not found in environment, try to read from config.yml
    try:
        with open("config.yml", "r", encoding='utf-8') as config_file:
            config_data = yaml.load(config_file, Loader=yaml.FullLoader)
            return config_data
    except FileNotFoundError:
        return default_value
    
sentry_sdk.init(
    dsn="https://604a3646906493f26e9772bc76086df7@us.sentry.io/4506698716348416",
)

conf = ReadConf('SRC_CONFIG')['accounts']

if not conf:
    print('请正确配置环境变量或者config.yml后再运行本脚本！')
    os._exit(0)
print(f'检测到 {len(conf)} 个账号，正在进行任务……')

class RunError(Exception):
    pass


try:
    ver_info = r.get('https://api-launcher-static.mihoyo.com/hkrpg_cn/mdk/launcher/api/resource?channel_id=1&key=6KcVuOkbcqjJomjZ&launcher_id=33&sub_channel_id=2', timeout=60).text
    version = json.loads(ver_info)['data']['game']['latest']['version']
    print(f'从官方API获取到云·星穹铁道最新版本号：{version}')
except:
    version = '2.0.0'

NotificationURL = 'https://cg-hkrpg-api.mihoyo.com/hkrpg_cn/cg/gamer/api/listNotifications?status=NotificationStatusUnread&type=NotificationTypePopup&is_sort=true'
WalletURL = 'https://cg-hkrpg-api.mihoyo.com/hkrpg_cn/cg/wallet/wallet/get?cost_method=0'
AnnouncementURL = 'https://cg-hkrpg-api.mihoyo.com/hkrpg_cn/cg/gamer/api/getAnnouncementInfo'

if __name__ == '__main__':
    for config in conf:
        if config == '':
            # Verify config
            raise RunError(
                f"请在Settings->Secrets->Actions页面中新建名为SRC_CONFIG的变量，并将你的配置填入后再运行！")
        else:
            token = config['token']
            client_type = config['type']
            sysver = config['sysver']
            deviceid = config['deviceid']
            devicename = config['devicename']
            devicemodel = config['devicemodel']
            appid = config['appid']
        headers = {
            'x-rpc-combo_token': token,
            'x-rpc-client_type': str(client_type),
            'x-rpc-app_version': str(version),
            'x-rpc-sys_version': str(sysver),  # Previous version need to convert the type of this var
            'x-rpc-channel': 'mihoyo',
            'x-rpc-device_id': deviceid,
            'x-rpc-device_name': devicename,
            'x-rpc-device_model': devicemodel,
            'x-rpc-vendor_id': '2',
            'x-rpc-cg_game_biz': 'hkrpg_cn',
            'x-rpc-op_biz': 'clgm_hkrpg-cn',
            'x-rpc-language': 'zh-cn',
            'x-rpc-cg_game_id': '9000096',
            'Host': 'cg-hkrpg-api.mihoyo.com',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0'
        }
        bbsid = re.findall(r'oi=[0-9]+', token)[0].replace('oi=', '')
        wait_time = random.randint(1, 3600) # Random Sleep to Avoid Ban
        print(f'为了避免同一时间签到人数太多导致被官方怀疑，开始休眠 {wait_time} 秒')
        time.sleep(wait_time)
        wallet = r.get(WalletURL, headers=headers, timeout=60)
        if json.loads(wallet.text) == {"data": None,"message":"登录已失效，请重新登录","retcode":-100}: 
            print(f'当前登录已过期，请重新登陆！返回为：{wallet.text}')
        else:
            print(
                f"你当前拥有免费时长 {json.loads(wallet.text)['data']['free_time']['free_time']} 分钟，畅玩卡状态为 {json.loads(wallet.text)['data']['play_card']['short_msg']}，拥有米云币 {json.loads(wallet.text)['data']['coin']['coin_num']} 枚")
            announcement = r.get(AnnouncementURL, headers=headers, timeout=60)
            print(f'获取到公告列表：{json.loads(announcement.text)["data"]}')
            res = r.get(NotificationURL, headers=headers, timeout=60)
            success,Signed = False,False
            try:
                if list(json.loads(res.text)['data']['list']) == []:
                    success = True
                    Signed = True
                    Over = False
                elif json.loads(json.loads(res.text)['data']['list'][0]['msg']) == {"num": 15, "over_num": 0, "type": 2, "msg": "每日登录奖励", "func_type": 1}:
                    success = True
                    Signed = False
                    Over = False
                elif json.loads(json.loads(res.text)['data']['list'][0]['msg'])['over_num'] > 0:
                    success = True
                    Signed = False
                    Over = True
                else:
                    success = False
            except IndexError:
                success = False
            if success:
                if Signed:
                    print(
                        f'获取签到情况成功！今天是否已经签到过了呢？')
                    print(f'完整返回体为：{res.text}')
                elif not Signed and Over:
                    print(
                        f'获取签到情况成功！当前免费时长已经达到上限！签到情况为{json.loads(res.text)["data"]["list"][0]["msg"]}')
                    print(f'完整返回体为：{res.text}')
                else:
                    print(
                        f'获取签到情况成功！当前签到情况为{json.loads(res.text)["data"]["list"][0]["msg"]}')
                    print(f'完整返回体为：{res.text}')
            else:
                raise RunError(
                    f"签到失败！请带着本次运行的所有log内容到 https://github.com/GamerNoTitle/SRCloud-AutoCheckin 发起issue解决（或者自行解决）。签到出错，返回信息如下：{res.text}")
