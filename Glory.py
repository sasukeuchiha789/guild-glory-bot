import ssl
import asyncio
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import aiohttp
import MajorLoginReq_pb2
import MajorLoginRes_pb2
import GetLoginDataRes_pb2
import DecodeWhisperMsg_pb2
import GenWhisperMsg_pb2
from datetime import datetime
import recieved_chat_pb2
import Anti_Afk_pb2
import json
from protobuf_decoder.protobuf_decoder import Parser
import bot_mode_pb2
import bot_invite_pb2
import base64
import random_pb2
from threading import Thread
import Clan_Startup_pb2
import recieved_chat_pb2
import random
import pytz
import root
import engine
import time
import re
import telebot
from telebot import types
import asyncio

# Initialize Telegram bot
bot = telebot.TeleBot("8450600137:AAFxpXdkhtXW3i6FIk0EgWpoZsKIvTH7nb8")



# <--- FIX: Make writers globally accessible --->
online_writer = None
whisper_writer = None

headers = {
    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 11; ASUS_Z01QD Build/PI)",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "gzip",
    'Content-Type': "application/x-www-form-urlencoded",
    'Expect': "100-continue",
    'X-Unity-Version': "2018.4.11f1",
    'X-GA': "v1 1",
    'ReleaseVersion': "OB51"
}


TOKEN_EXPIRY = 7 * 60 * 60
# <-------------------------------------------------------------------------------------------->


async def encrypted_proto(encoded_hex):
    key = b'Yg&tc%DEuh6%Zc^8'
    iv = b'6oyZDr22E3ychjM%'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_message = pad(encoded_hex, AES.block_size)
    encrypted_payload = cipher.encrypt(padded_message)
    return encrypted_payload

async def get_random_user_agent():
    versions = [
        '4.0.18P6', '4.0.19P7', '4.0.20P1', '4.1.0P3', '4.1.5P2', '4.2.1P8',
        '4.2.3P1', '5.0.1B2', '5.0.2P4', '5.1.0P1', '5.2.0B1', '5.2.5P3',
        '5.3.0B1', '5.3.2P2', '5.4.0P1', '5.4.3B2', '5.5.0P1', '5.5.2P3'
    ]
    models = [
        'SM-A125F', 'SM-A225F', 'SM-A325M', 'SM-A515F', 'SM-A725F', 'SM-M215F', 'SM-M325FV',
        'Redmi 9A', 'Redmi 9C', 'POCO M3', 'POCO M4 Pro', 'RMX2185', 'RMX3085',
        'moto g(9) play', 'CPH2239', 'V2027', 'OnePlus Nord', 'ASUS_Z01QD',
    ]
    android_versions = ['9', '10', '11', '12', '13', '14']
    languages = ['en-US', 'es-MX', 'pt-BR', 'id-ID', 'ru-RU', 'hi-IN']
    countries = ['USA', 'MEX', 'BRA', 'IDN', 'RUS', 'IND']
    version = random.choice(versions)
    model = random.choice(models)
    android = random.choice(android_versions)
    lang = random.choice(languages)
    country = random.choice(countries)
    return f"GarenaMSDK/{version}({model};Android {android};{lang};{country};)"

async def get_access_token(uid, password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    headers = {
        "Host": "100067.connect.garena.com",
        "User-Agent": (await get_random_user_agent()),
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "close"
    }
    data = {
        "uid": uid,
        "password": password,
        "response_type": "token",
        "client_type": "2",
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as response:
            if response.status != 200:
                return "Failed to get access token"
            data = await response.json()
            open_id = data.get("open_id")
            access_token = data.get("access_token")
            return (open_id, access_token) if open_id and access_token else (None, None)

async def MajorLoginProto_Encode(open_id, access_token):
    major_login = MajorLoginReq_pb2.MajorLogin()
    major_login.event_time = "2025-06-04 19:48:07"
    major_login.game_name = "free fire"
    major_login.platform_id = 1
    major_login.client_version = "1.118.1"
    major_login.system_software = "Android OS 9 / API-28 (PQ3B.190801.10101846/G9650ZHU2ARC6)"
    major_login.system_hardware = "Handheld"
    major_login.telecom_operator = "Verizon"
    major_login.network_type = "WIFI"
    major_login.screen_width = 1920
    major_login.screen_height = 1080
    major_login.screen_dpi = "280"
    major_login.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    major_login.memory = 3003
    major_login.gpu_renderer = "Adreno (TM) 640"
    major_login.gpu_version = "OpenGL ES 3.1 v1.46"
    major_login.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    major_login.client_ip = "223.191.51.89"
    major_login.language = "en"
    major_login.open_id = open_id
    major_login.open_id_type = "4"
    major_login.device_type = "Handheld"
    memory_available = major_login.memory_available
    memory_available.version = 55
    memory_available.hidden_value = 81
    major_login.access_token = access_token
    major_login.platform_sdk_id = 1
    major_login.network_operator_a = "Verizon"
    major_login.network_type_a = "WIFI"
    major_login.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    major_login.external_storage_total = 36235
    major_login.external_storage_available = 31335
    major_login.internal_storage_total = 2519
    major_login.internal_storage_available = 703
    major_login.game_disk_storage_available = 25010
    major_login.game_disk_storage_total = 26628
    major_login.external_sdcard_avail_storage = 32992
    major_login.external_sdcard_total_storage = 36235
    major_login.login_by = 3
    major_login.library_path = "/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/lib/arm64"
    major_login.reg_avatar = 1
    major_login.library_token = "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/base.apk"
    major_login.channel_type = 3
    major_login.cpu_type = 2
    major_login.cpu_architecture = "64"
    major_login.client_version_code = "2029123000"
    major_login.graphics_api = "OpenGLES2"
    major_login.supported_astc_bitset = 16383
    major_login.login_open_id_type = 4
    major_login.analytics_detail = b"FwQVTgUPX1UaUllDDwcWCRBpWAUOUgsvA1snWlBaO1kFYg=="
    major_login.loading_time = 13564
    major_login.release_channel = "android"
    major_login.extra_info = "KqsHTymw5/5GB23YGniUYN2/q47GATrq7eFeRatf0NkwLKEMQ0PK5BKEk72dPflAxUlEBir6Vtey83XqF593qsl8hwY="
    major_login.android_engine_init_flag = 110009
    major_login.if_push = 1
    major_login.is_vpn = 1
    major_login.origin_platform_type = "4"
    major_login.primary_platform_type = "4"
    string = major_login.SerializeToString()
    return  await encrypted_proto(string)

async def MajorLogin(payload):
    url = "https://loginbp.common.ggbluefox.com/MajorLogin"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=headers, ssl=ssl_context) as response:
            if response.status == 200:
                return await response.read()
            return None

async def GetLoginData(base_url, payload, token):
    url = f"{base_url}/GetLoginData"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    headers['Authorization']= f"Bearer {token}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=headers, ssl=ssl_context) as response:
            if response.status == 200:
                return await response.read()
            return None

API_KEYS = [
    "AIzaSyA8IiZS4SgA1DocEG1GA318a4baKvEWYBc",
    "AIzaSyCCr2sq-s1bWEwuK0ZIv8ITkqccxzMMCDI",
    "AIzaSyCLF8o66saIX9lKRzWt8RW9HjFZ1N8W6H0",
    "AIzaSyCM7zVQ9FM_BKI15O6Hgc6NN5F3RK3Xa0o",
    "AIzaSyCkiYnzLsWomUiRo4v6zWMx3X3yuoObRRM"
]

chat_history = [
    {
        "role": "user",
        "parts": [{"text": "You are a helpful assistant."}]
    }
]

key_index = 0

async def Get_AI_Response(user_input):
    global key_index

    # Append user message with extra instruction
    chat_history.append({
        "role": "user",
        "parts": [
            {"text": user_input},
            {"text": "Remove markdown and HTML from the output"}
        ]
    })

    headers = {"Content-Type": "application/json"}

    for _ in range(len(API_KEYS)):
        api_key = API_KEYS[key_index]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {"contents": chat_history}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                result = await response.json()

                if "candidates" in result:
                    reply = result["candidates"][0]["content"]["parts"][0]["text"]
                    chat_history.append({
                        "role": "model",
                        "parts": [{"text": reply}]
                    })
                    return reply
                elif result.get("error", {}).get("code") == 429:
                    key_index = (key_index + 1) % len(API_KEYS)
                    print("⚠️ Switching API key due to rate limit.")
                    await asyncio.sleep(1)
                else:
                    return "Failed to get response: " + str(result)

    return "All keys reached rate limit."

async def MajorLogin_Decode(MajorLoginResponse):
    proto = MajorLoginRes_pb2.MajorLoginRes()
    proto.ParseFromString(MajorLoginResponse)
    return proto

async def GetLoginData_Decode(GetLoginDataResponse):
    proto = GetLoginDataRes_pb2.GetLoginData()
    proto.ParseFromString(GetLoginDataResponse)
    return proto

async def decode_team_packet(hex_packet):
    packet = bytes.fromhex(hex_packet)
    proto = recieved_chat_pb2.recieved_chat()
    proto.ParseFromString(packet)
    return proto

async def DecodeWhisperMessage(hex_packet):
    try:
        packet = bytes.fromhex(hex_packet)
        proto = DecodeWhisperMsg_pb2.DecodeWhisper()
        proto.ParseFromString(packet)
        return proto
    except Exception as e:
        print(f"[DecodeWhisperMessage Error] {e}")
        return None

async def base_to_hex(timestamp):
    timestamp_result = hex(timestamp)
    result = str(timestamp_result)[2:]
    if len(result) == 1:
        result = "0" + result
    return result

async def parse_results(parsed_results):
    result_dict = {}
    for result in parsed_results:
        field_data = {}
        field_data["wire_type"] = result.wire_type
        if result.wire_type == "varint":
            field_data["data"] = result.data
        if result.wire_type == "string":
            field_data["data"] = result.data
        if result.wire_type == "bytes":
            field_data["data"] = result.data
        elif result.wire_type == "length_delimited":
            field_data["data"] = await parse_results(result.data.results)
        result_dict[result.field] = field_data
    return result_dict

async def split_text_by_words(text, max_length=200):
    def insert_c_in_number(word):
        if word.isdigit():
            mid = len(word) // 2
            return word[:mid] + "[C]" + word[mid:]
        return word

    words = text.split()
    words = [insert_c_in_number(word) for word in words]

    chunks = []
    current = ""

    for word in words:
        if len(current) + len(word) + (1 if current else 0) <= max_length:
            current += (" " if current else "") + word
        else:
            chunks.append(current)
            current = word

    if current:
        chunks.append(current)

    return chunks

async def get_available_room(input_text):
    try:
        parsed_results = Parser().parse(input_text)
        parsed_results_objects = parsed_results
        parsed_results_dict = await parse_results(parsed_results_objects)
        json_data = json.dumps(parsed_results_dict)
        return json_data
    except Exception as e:
        print(f"error {e}")
        return None

async def team_chat_startup(player_uid, team_session, key, iv):
    proto = Team_Chat_Startup_pb2.team_chat_startup()
    proto.field1 = 3
    proto.details.uid = player_uid
    proto.details.language = "en"
    proto.details.team_packet = team_session

    packet = proto.SerializeToString().hex()
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)

    if len(packet_length_hex) == 2:
        final_packet = "1201000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "120100000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "12010000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "1201000" + packet_length_hex + encrypted_packet
    else:
        print("something went wrong, please check clan startup function.")
    if whisper_writer: # <--- FIX: Check if writer is available  
        whisper_writer.write(bytes.fromhex(final_packet))
        await whisper_writer.drain()

async def encrypt_packet(packet, key, iv):
    bytes_packet = bytes.fromhex(packet)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    cipher_text = cipher.encrypt(pad(bytes_packet, AES.block_size))
    return cipher_text.hex()

async def create_clan_startup(clan_id, clan_compiled_data, key, iv):
    proto = Clan_Startup_pb2.ClanPacket()
    proto.Clan_Pos = 3
    proto.Data.Clan_ID = int(clan_id)
    proto.Data.Clan_Type = 1
    proto.Data.Clan_Compiled_Data = clan_compiled_data
    packet = proto.SerializeToString().hex()
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)
    if len(packet_length_hex) == 2:
        final_packet = "1201000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "120100000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "12010000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "1201000" + packet_length_hex + encrypted_packet
    else:
        print("something went wrong, please check clan startup function.")
    if whisper_writer: # <--- FIX: Check if writer is available
        whisper_writer.write(bytes.fromhex(final_packet))
        await whisper_writer.drain()

async def create_group(key, iv):
    packet = "080112bc04120101180120032a02656e420d0a044944433110661a03494e444801520601090a121920580168017288040a403038303230303032433733464233454430323031303030303030303030303030303030303030303030303030303030303137424236333544303930303030303010151a8f0375505d5413070448565556000b5009070405500303560a08030354550007550f02570d03550906521702064e76544145491e0418021e11020b4d1a42667e58544776725757486575441f5a584a065b46426a5a65650e14034f7e5254047e005a7b7c555c0d5562637975670a7f765b0102537906091702044e72747947457d0d6267456859587b596073435b7205046048447d080b170c4f584a6b007e4709740661625c545b0e7458405f5e4e427f486652420c13070c484b597a717a5a5065785d4343535d7c7a6450675a787e05736418010c12034a475b71717a566360437170675a6b1c740748796065425e017e4f5d0e1a034d09660358571843475c774b5f524d47670459005a4870780e795e7a0a110a457e5e5a00776157597069094266014f716d7246754a60506b747404091005024f7e765774035967464d687c724703075d4e76616f7a184a7f057a6f0917064b5f797d05434250031b0555717b0d00611f59027e60077b4a0a5c7c0d1500480143420b5a65746803636e41556a511269087e4f5f7f675c0440600c22047c5c5754300b3a1a16024a424202050607021316677178637469785d51745a565a5a4208312e3130392e3136480650029801c902aa01024f52"
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)
    if len(packet_length_hex) == 2:
        final_packet = "0514000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "051400000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    else:
        print("something went wrong, please check create_group function.")
    if online_writer: # <--- FIX: Check if writer is available
        online_writer.write(bytes.fromhex(final_packet))
        await online_writer.drain()
  
              
async def wlxd_skwad(uid, key, iv):
    packet = wlxd_spam_pb2.invite_uid()
    #packet.field1 = 33

    #details = packet.field2
    details.user_id = int(uid)
    details.country_code = "IND"
    details.status1 = 1
    details.status2 = 1
    details.numbers = bytes([16, 21, 8, 10, 11, 19, 12, 15, 17, 4, 7, 2, 3, 13, 14, 18, 1, 5, 6])
    details.empty1 = ""
    details.rank = 330
    details.field8 = 6000
    details.field9 = 100
    details.region_code = "IND"
    details.uuid = bytes([
                55, 52, 50, 56, 98, 50, 53, 51, 100, 101, 102, 99,
                49, 54, 52, 48, 49, 56, 99, 54, 48, 52, 97, 49,
                101, 98, 98, 102, 101, 98, 100, 102
            ])
    details.field12 = 1
    details.repeated_uid = int(uid)
    details.field16 = 1
    details.field18 = 228
    details.field19 = 22

    nested = details.field20
    nested.server = "IDC1"
    nested.ping = 3000
    nested.country = "IND"

    details.field23 = bytes([16, 1, 24, 1])
    details.avatar = int(get_random_avatar())

    # field26 and field28 are empty messages
    details.field26.SetInParent()
    details.field28.SetInParent()

    # Serialize, encrypt, and send the packet
    serialized = packet.SerializeToString().hex()
    encrypted_packet = await encrypt_packet(serialized, key, iv)

    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)

    if len(packet_length_hex) == 2:
        final_packet = "0514000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "051400000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    else:
        print("❌ Packet length formatting failed.")
        return

    online_writer.write(bytes.fromhex(final_packet))
    await online_writer.drain()

async def modify_team_player(team, key, iv):
    bot_mode = bot_mode_pb2.BotMode()
    bot_mode.key1 = 17
    bot_mode.key2.uid = 7669969208
    bot_mode.key2.key2 = 1
    bot_mode.key2.key3 = int(team)
    bot_mode.key2.key4 = 62
    bot_mode.key2.byte = base64.b64decode("Gg==")
    bot_mode.key2.key8 = 5
    bot_mode.key2.key13 = 227
    packet = bot_mode.SerializeToString().hex()
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)
    if len(packet_length_hex) == 2:
        final_packet = "0514000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "051400000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    else:
        print("something went wrong, please check create_group function.")
    if online_writer: # <--- FIX: Check if writer is available
        online_writer.write(bytes.fromhex(final_packet))
        await online_writer.drain()

async def invite_target(uid, key, iv):
    invite = bot_invite_pb2.invite_uid()
    invite.num = 2
    invite.Func.uid = int(uid)
    invite.Func.region = "IND"
    invite.Func.number = 1
    packet = invite.SerializeToString().hex()
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)
    if len(packet_length_hex) == 2:
        final_packet = "0514000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "051400000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    else:
        print("something went wrong, please check create_group function.")
    if online_writer: # <--- FIX: Check if writer is available
        online_writer.write(bytes.fromhex(final_packet))
        await online_writer.drain()

async def left_group(key, iv):
    packet = "0807120608da89d98d27"
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)
    if len(packet_length_hex) == 2:
        final_packet = "0514000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "051400000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "05140000" + packet_length_hex + encrypted_packet
    else:
        print("something went wrong, please check create_group function.")
    if online_writer: # <--- FIX: Check if writer is available
        online_writer.write(bytes.fromhex(final_packet))
        await online_writer.drain()

async def join_room(uid, room_id, key, iv):
    root = spam_join_pb2.spam_join()
    root.field_1 = 78
    root.field_2.field_1 = int(room_id)
    root.field_2.name = "[C][B][FF0000]TEAM-[00FF00]DEV"
    root.field_2.field_3.field_2 = 1
    root.field_2.field_3.field_3 = 1
    root.field_2.field_4 = 330
    root.field_2.field_5 = 6000
    root.field_2.field_6 = 201
    root.field_2.field_10 = get_random_avatar()
    root.field_2.field_11 = int(uid)
    root.field_2.field_12 = 1
    packet = root.SerializeToString().hex()
    packet_encrypt = await encrypt_packet(packet, key, iv)
    base_len = await base_to_hex(int(len(packet_encrypt) // 2))
    if len(base_len) == 2:
        header = "0e15000000"
    elif len(base_len) == 3:
        header = "0e1500000"
    elif len(base_len) == 4:
        header = "0e150000"
    elif len(base_len) == 5:
        header = "0e15000"
    final_packet = header + base_len + packet_encrypt
    online_writer.write(bytes.fromhex(final_packet))
    await online_writer.drain()

async def send_clan_msg(msg, chat_id, key, iv):
    root = clan_msg_pb2.clan_msg()
    root.type = 1
    nested_object = root.data
    nested_object.uid = 9119828499
    nested_object.chat_id = chat_id
    nested_object.chat_type = 1
    nested_object.msg = msg
    nested_object.timestamp = int(datetime.now().timestamp())
    nested_object.language = "en"
    nested_object.empty_field.SetInParent()
    nested_details = nested_object.field9
    nested_details.Player_Name = "Ɗᴇᴠ-ʙᴏᴛ"
    nested_details.avatar_id = get_random_avatar()
    nested_details.banner_id = 901000173
    nested_details.rank = 330
    nested_details.badge = 102000015
    nested_details.Clan_Name = "BOTSㅤARMY"
    nested_details.field10 = 1
    nested_details.rank_point = 1
    nested_badge = nested_details.field13
    nested_badge.value = 2
    nested_prime = nested_details.field14
    nested_prime.prime_uid = 1158053040
    nested_prime.prime_level = 8
    nested_prime.prime_hex = "\u0010\u0015\b\n\u000b\u0015\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"
    nested_options = nested_object.field13
    nested_options.url = "https://graph.facebook.com/v9.0/147045590125499/picture?width=160&height=160"
    nested_options.url_type = 1
    nested_options.url_platform = 1
    packet = root.SerializeToString().hex()
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    hex_length = await base_to_hex(packet_length)
    if len(hex_length) == 2:
        final_packet = "1215000000" + hex_length + encrypted_packet
    elif len(hex_length) == 3:
        final_packet = "121500000" + hex_length + encrypted_packet
    elif len(hex_length) == 4:
        final_packet = "12150000" + hex_length + encrypted_packet
    elif len(hex_length) == 5:
        final_packet = "1215000" + hex_length + encrypted_packet
    return bytes.fromhex(final_packet)

# <--- CORRECTED FUNCTION as requested--->
async def join_teamcode(room_id, key, iv):
    room_id_hex = ''.join(format(ord(c), 'x') for c in room_id)
    packet = f"080412b305220601090a1219202a07{room_id_hex}300640014ae8040a80013038304639324231383633453135424630323031303130303030303030303034303031363030303130303131303030323944373931333236303930303030353934313732323931343030303030303030303030303030303030303030303030303030303030303030303030303030666630303030303030306639396130326538108f011abf0377505d571709004d0b060b070b5706045c53050f065004010902060c09065a530506010851070a081209064e075c5005020808530d0604090b05050d0901535d030204005407000c5653590511000b4d5e570e02627b6771616a5560614f5e437f7e5b7f580966575b04010514034d7d5e5b465078697446027a7707506c6a5852526771057f5260504f0d1209044e695f0161074e46565a5a6144530174067a43694b76077f4a5f1d6d05130944664456564351667454766b464b7074065a764065475f04664652010f1709084d0a4046477d4806661749485406430612795b724e7a567450565b010c1107445e5e72780708765b460c5e52024c5f7e5349497c056e5d6972457f0c1a034e60757840695275435f651d615e081e090e75457e7464027f5656750a1152565f545d5f1f435d44515e57575d444c595e56565e505b555340594c5708740b57705c5b5853670957656a03007c04754c627359407c5e04120b4861037b004f6b744001487d506949796e61406a7c44067d415b0f5c0f120c4d54024c6a6971445f767d4873076e5f48716f537f695a7365755d520514064d515403717b72034a027d736b6053607e7553687a61647d7a686c610d22047c5b5655300b3a0816647b776b721c144208312e3130382e3134480350025a0c0a044944433110731a0242445a0c0a044944433210661a0242445a0c0a044944433310241a0242446a02656e8201024f52"
    encrypted_packet = await encrypt_packet(packet, key, iv)
    packet_length = len(encrypted_packet) // 2
    packet_length_hex = await base_to_hex(packet_length)

    if len(packet_length_hex) == 2:
        final_packet = "0519000000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 3:
        final_packet = "051900000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 4:
        final_packet = "05190000" + packet_length_hex + encrypted_packet
    elif len(packet_length_hex) == 5:
        final_packet = "05190000" + packet_length_hex + encrypted_packet
    else:
        print("Damm Something went wrong, please check join teamcode function")
    if online_writer: # <--- FIX: Check if writer is available
        online_writer.write(bytes.fromhex(final_packet))
        await online_writer.drain()

async def send_team_msg(msg, chat_id, key, iv):
     root = Team_msg_pb2.clan_msg()
     root.type = 1
     nested_object = root.data
     nested_object.uid = 9119828499
     nested_object.chat_id = chat_id
     nested_object.msg = msg
     nested_object.timestamp = int(datetime.now().timestamp())
     nested_object.chat_type = 2
     nested_object.language = "en"
     nested_details = nested_object.field9
     nested_details.Player_Name = "Ɗᴇᴠ-ʙᴏᴛ"
     nested_details.avatar_id = get_random_avatar()
     nested_details.rank = 330
     #nested_details.badge = 102000015
     nested_details.Clan_Name = "BOTSㅤARMY"
     nested_details.field10 = 1
     #nested_details.global_rank_pos = 1
     #nested_details.badge_info.value = 2  # Example value
     #nested_details.prime_info.prime_uid = 1158053040
     #nested_details.prime_info.prime_level = 8
     #nested_details.prime_info.prime_hex = "\u0010\u0015\b\n\u000b\u0015\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"
     nested_options = nested_object.field13
     nested_options.url_type = 2
     nested_options.url_platform = 1
     nested_object.empty_field.SetInParent()
     packet = root.SerializeToString().hex()
     encrypted_packet = await encrypt_packet(packet, key, iv)
     packet_length = len(encrypted_packet) // 2
     hex_length = await base_to_hex(packet_length)
     packet_prefix = "121500" + "0" * (6 - len(hex_length))
     final_packet = packet_prefix + hex_length + encrypted_packet
     return bytes.fromhex(final_packet)

async def send_msg(msg, chat_id, key, iv):
     root = GenWhisperMsg_pb2.GenWhisper()
     root.type = 1
     nested_object = root.data
     nested_object.uid = 9119828499
     nested_object.chat_id = chat_id
     nested_object.chat_type = 2
     nested_object.msg = msg
     nested_object.timestamp = int(datetime.now().timestamp())
     nested_details = nested_object.field9
     nested_details.Nickname = "Ɗᴇᴠ-ʙᴏᴛ"
     nested_details.avatar_id = get_random_avatar()
     nested_details.banner_id = 901000173
     nested_details.rank = 330
     nested_details.badge = 102000015
     nested_details.Clan_Name = "BOTSㅤARMY"
     nested_details.field10 = 1
     nested_details.global_rank_pos = 1
     nested_badge = nested_details.field13
     nested_badge.value = 2  # Example value
     nested_prime = nested_details.field14
     nested_prime.prime_uid = 1158053040
     nested_prime.prime_level = 8
     nested_prime.prime_hex = "\u0010\u0015\b\n\u000b\u0015\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"
     nested_options = nested_object.field13
     nested_object.language = "en"
     nested_options = nested_object.field13
     nested_options.url = "https://graph.facebook.com/v9.0/147045590125499/picture?width=160&height=160"
     nested_options.url_type = 2
     nested_options.url_platform = 1
     root.data.Celebrity = 1919408565318037500
     root.data.empty_field.SetInParent()
     packet = root.SerializeToString().hex()
     encrypted_packet = await encrypt_packet(packet, key, iv)
     packet_length = len(encrypted_packet) // 2
     hex_length = await base_to_hex(packet_length)

     if len(hex_length) == 2:
         final_packet = "1215000000" + hex_length + encrypted_packet
     elif len(hex_length) == 3:
         final_packet = "121500000" + hex_length + encrypted_packet
     elif len(hex_length) == 4:
         final_packet = "12150000" + hex_length + encrypted_packet
     elif len(hex_length) == 5:
         final_packet = "1215000" + hex_length + encrypted_packet

     return bytes.fromhex(final_packet)

async def get_encrypted_startup(AccountUID, token, timestamp, key, iv):
    uid_hex = hex(AccountUID)[2:]
    uid_length = len(uid_hex)
    encrypted_timestamp = await base_to_hex(timestamp)
    encrypted_account_token = token.encode().hex()
    encrypted_packet = await encrypt_packet(encrypted_account_token, key, iv)
    encrypted_packet_length = hex(len(encrypted_packet) // 2)[2:]

    if uid_length == 7:
        headers = '000000000'
    elif uid_length == 8:
        headers = '00000000'
    elif uid_length == 9:
        headers = '0000000'
    elif uid_length == 10:
        headers = '000000'
    elif uid_length == 11:
        headers = '00000'
    else:
        print('Unexpected length, Please Try again')
        headers = '0000000' # Default fallback

    packet = f"0115{headers}{uid_hex}{encrypted_timestamp}00000{encrypted_packet_length}{encrypted_packet}"
    return packet

async def Encrypt(number):
    number = int(number)
    encoded_bytes = []

    while True:
        byte = number & 0x7F
        number >>= 7
        if number:
            byte |= 0x80

        encoded_bytes.append(byte)
        if not number:
            break
    return bytes(encoded_bytes).hex()

async def uid_status(uid, key, iv):
    uid_text = {await Encrypt(uid)}
    uid_hex = next(iter(uid_text))
    packet = f"080112e8010ae301afadaea327bfbd809829a8fe89db07eda4c5f818f8a485850eefb3a39e06{uid_hex}ecb79fd623e4b3c0f506c6bdc48007d4efbc7ce688be8709c99ef7bc02e0a8bcd607d6ebe8e406dcc9a6ae07bfdab0e90a8792c28d08b58486f528cfeff0c61b95fcee8b088f96da8903effce2b726b684fbe10abfe984db28bbfebca528febd8dba28ecb98cb00baeb08de90583f28a9317a5ced6ab01d3de8c71d3a1b1be01ede292e907e5ecd0b903b2cafeae04c098fae5048cfcc0cd18d798b5f401cd9cbb61e8dce3c00299b895de1184e9c9ee11c28ed0d803f8b7ffec02a482babd011001"

    encrypted_packet = await encrypt_packet(packet, key, iv)
    header_length = len(encrypted_packet) // 2

    header_length_hex = await base_to_hex(header_length)

    if len(header_length_hex) == 2:
        final_packet = "0f15000000" + header_length_hex + encrypted_packet
    elif len(header_length_hex) == 3:
        final_packet = "0f1500000" + header_length_hex + encrypted_packet
    elif len(header_length_hex) == 4:
        final_packet = "0f150000" + header_length_hex + encrypted_packet
    elif len(header_length_hex) == 5:
        final_packet = "0f150000" + header_length_hex + encrypted_packet
    else:
        raise ValueError("error 505")

    if online_writer: # <--- FIX: Check if writer is available
        online_writer.write(bytes.fromhex(final_packet))
        await online_writer.drain()

async def handle_tcp_online_connection(ip, port, key, iv, encrypted_startup, reconnect_delay=0):
    global online_writer, spam_room, whisper_writer, spammer_uid, spam_chat_id, spam_uid
    while True:
        try:
            reader, writer = await asyncio.open_connection(ip, int(port))
            online_writer = writer

            bytes_payload = bytes.fromhex(encrypted_startup)
            online_writer.write(bytes_payload)
            await online_writer.drain()

            while True:
                data = await reader.read(9999)
                if not data:
                    break
                if data.hex().startswith("0f00"):
                    if spam_room:
                        try:
                            json_result = await get_available_room(data.hex()[10:])
                            if json_result:
                                parsed_data = json.loads(json_result)
                                if "5" in parsed_data and "data" in parsed_data["5"] and \
                                   "1" in parsed_data["5"]["data"] and "data" in parsed_data["5"]["data"]["1"] and \
                                   "15" in parsed_data["5"]["data"]["1"]["data"] and "data" in parsed_data["5"]["data"]["1"]["data"]["15"]:

                                    room_id = parsed_data["5"]["data"]["1"]["data"]["15"]["data"]
                                    uid = parsed_data["5"]["data"]["1"]["data"]["1"]["data"]
                                    spam_room = False
                                    message = f"Spamming on\n\nRoom ID: {str(room_id)[:5]}[C]{str(room_id)[5:]}\nUID: {str(uid)[:5]}[C]{str(uid)[5:]}"
                                    if spam_chat_id == 1:
                                        msg_packet = await send_team_msg(message, spam_uid, key, iv)
                                    elif spam_chat_id == 2:
                                        msg_packet = await send_clan_msg(message, spam_uid, key, iv)
                                    else:
                                        msg_packet = await send_msg(message, spam_uid, key, iv)
                                    if whisper_writer:
                                        whisper_writer.write(msg_packet)
                                        await whisper_writer.drain()
                                    
                                    # Add 1-minute delay with 0.1 second intervals
                                    start_time = time.time()
                                    while time.time() - start_time < 300:  # 120 seconds = 1 minute
                                        await join_room(uid, room_id, key, iv)
                                        await asyncio.sleep(0.25)  # 0.01 second delay
                                    
                                else:
                                    message = "Player not in room"
                                    if spam_chat_id == 1:
                                        msg_packet = await send_team_msg(message, spam_uid, key, iv)
                                    elif spam_chat_id == 2:
                                        msg_packet = await send_clan_msg(message, spam_uid, key, iv)
                                    else:
                                        msg_packet = await send_msg(message, spam_uid, key, iv)
                                    if whisper_writer:
                                        whisper_writer.write(msg_packet)
                                        await whisper_writer.drain()
                                    spam_room = False
                        except Exception as e:
                            print(f"Error processing room data: {e}")
                            spam_room = False

                elif data.hex().startswith("0500000"):
                    try:
                        response = await decode_team_packet(data.hex()[10:])
                        if response.packet_type == 6:
                            await team_chat_startup(response.details.player_uid, response.details.team_session, key, iv)
                    except Exception as e:
                        pass

            online_writer.close()
            await online_writer.wait_closed()
            online_writer = None

        except Exception as e:
            print(f"Error with {ip}:{port} - {e}")
            online_writer = None

        await asyncio.sleep(reconnect_delay)

async def handle_tcp_connection(ip, port, encrypted_startup, key_param, iv_param, Decode_GetLoginData, ready_event, reconnect_delay=0.5):    
    global spam_room, whisper_writer, spammer_uid, spam_chat_id, spam_uid, online_writer, key, iv    
    key = key_param    
    iv = iv_param    
    
    async def send_response(message, uid, chat_id, chat_type):
        """Helper function to send responses based on chat type"""
        if chat_type == 0:  # Team chat
            msg_packet = await send_team_msg(message, uid, key, iv)
        elif chat_type == 1:  # Clan chat
            msg_packet = await send_clan_msg(message, chat_id, key, iv)
        else:  # Private message
            msg_packet = await send_msg(message, uid, key, iv)
        
        if whisper_writer:
            whisper_writer.write(msg_packet)
            await whisper_writer.drain()

    async def send_chunk(text, uid, chat_id, chat_type, delay=0.3):
        """Send long messages in chunks with delay"""
        chunks = [text[i:i+200] for i in range(0, len(text), 200)]
        for chunk in chunks:
            await send_response(chunk, uid, chat_id, chat_type)
            await asyncio.sleep(delay)

    while True:
        try:
            reader, writer = await asyncio.open_connection(ip, int(port))
            whisper_writer = writer  # Assign to the global writer

            # Send startup packet
            bytes_payload = bytes.fromhex(encrypted_startup)
            whisper_writer.write(bytes_payload)
            await whisper_writer.drain()
            ready_event.set()
            
            # Handle clan startup if needed
            if Decode_GetLoginData.Clan_ID:
                clan_id = Decode_GetLoginData.Clan_ID
                clan_compiled_data = Decode_GetLoginData.Clan_Compiled_Data
                await create_clan_startup(clan_id, clan_compiled_data, key, iv)

            # Main message handling loop
            while True:
                data = await reader.read(9999)
                if not data:
                    break
                    
                if data.hex().startswith("120000"):
                    response = await DecodeWhisperMessage(data.hex()[10:])
                    received_msg = response.Data.msg.lower()
                    uid = response.Data.uid
                    user_name = response.Data.Details.Nickname
                    chat_id = response.Data.Chat_ID
                    # Safe access: try direct, then inside Details, else default to 0
                    chat_type = getattr(response.Data, "chat_type", None) or getattr(response.Data.Details, "chat_type", 0)

        except Exception as e:
            print(f"Error with {ip}:{port} - {e}")
            whisper_writer = None # <--- FIX: Clear global writer on error

        await asyncio.sleep(reconnect_delay)

async def main(uid, password):
    open_id, access_token = await get_access_token(uid, password)
    if not open_id or not access_token:
        print("Invalid Account")
        return None
    payload = await MajorLoginProto_Encode(open_id, access_token)
    MajorLoginResponse = await MajorLogin(payload)
    if not MajorLoginResponse:
        print("Account has been banned or doesn't registered")
        return None
    Decode_MajorLogin = await MajorLogin_Decode(MajorLoginResponse)
    base_url = Decode_MajorLogin.url
    token = Decode_MajorLogin.token
    AccountUID = Decode_MajorLogin.account_uid
    print(f"          \n═══════════════════════════════════════════════════════\n\n ~~ {AccountUID} BoT Connect To Guest Id Successfully ~~\n\n════════════════════════════════════════════════════════")
    key = Decode_MajorLogin.key
    iv = Decode_MajorLogin.iv
    timestamp = Decode_MajorLogin.timestamp
    GetLoginDataResponse = await GetLoginData(base_url, payload, token)
    if not GetLoginDataResponse:
        print("Dam Something went Wrong, Please Check GetLoginData")
        return None
    Decode_GetLoginData = await GetLoginData_Decode(GetLoginDataResponse)
    Online_IP_Port = Decode_GetLoginData.Online_IP_Port
    AccountIP_Port = Decode_GetLoginData.AccountIP_Port
    online_ip, online_port = Online_IP_Port.split(":")
    account_ip, account_port = AccountIP_Port.split(":")
    encrypted_startup = await get_encrypted_startup(int(AccountUID), token, int(timestamp), key, iv)

    ready_event = asyncio.Event()
    task1 = asyncio.create_task(
        handle_tcp_connection(account_ip, account_port, encrypted_startup, key, iv, Decode_GetLoginData, ready_event)
    )

    await ready_event.wait()
    await asyncio.sleep(2)

    task2 = asyncio.create_task(
        handle_tcp_online_connection(online_ip, online_port, key, iv, encrypted_startup)
    )

    await asyncio.gather(task1, task2)

    """Helper function to run async coroutines in sync context"""
    loop = asyncio.get_event_loop()
    return await loop.create_task(coro)

key = b'Yg&tc%DEuh6%Zc^8'
iv = b'6oyZDr22E3ychjM%'

event_loop = asyncio.new_event_loop()

def run_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


async def start_bot(uid, password):
    try:
        await asyncio.wait_for(main(uid, password), timeout=TOKEN_EXPIRY)
    except asyncio.TimeoutError:
        print("Token expired after 7 hours. Restarting...")
    except Exception as e:
        print(f" Error: {e}. Restarting...")

async def run_forever(uid, password):
    while True:
        await start_bot(uid, password)

def run_bot():
    asyncio.run(run_forever(
        "4379318083",
        "5837C9EA8805FB9CAFB431BF4F76EA59957E9F93EAE3AE837D98BDEFC353F9C4"
    ))

if __name__ == '__main__':
    import threading
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    bot.infinity_polling()
    app.run(host='Loacal', port=port)