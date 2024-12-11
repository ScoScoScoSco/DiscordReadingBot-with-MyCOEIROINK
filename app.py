import os
import json
import requests
from discord.ext import commands
import discord
from io import BytesIO
import re  # URLの検出に使用

TOKEN = 'paste your DiscordToken'

# 音声合成APIを使って音声ファイルを生成する関数
def talk(text):
    # リクエストボディ 
    text = re.sub(r'<.*?>', '', text)
    
    query = {
        "speakerUuid": "paste speakerUuid",
        "styleId": "paste your styleId",
        "text": text,
        "speedScale": 1.0,
        "volumeScale": 1.0,
        "prosodyDetail": [],
        "pitchScale": 0.0,
        "intonationScale": 1.0,
        "prePhonemeLength": 0.1,
        "postPhonemeLength": 0.5,
        "outputSamplingRate": 24000,
    }

    # 音声合成を実行
    response = requests.post(
        "http://127.0.0.1:50032/v1/synthesis",
        headers={"Content-Type": "application/json"},
        data=json.dumps(query),
    )

    response.raise_for_status()

    # 音声をメモリ内に保存し、返す
    return BytesIO(response.content)

# URLを検出し、テキストがURLのみの場合は「リンク省略」として返す関数
def process_message(text):
    url_pattern = r'https?://\S+|www\.\S+'  # URLパターン

    # テキストが完全にURLだけで構成されている場合は「リンク省略」を返す
    if re.fullmatch(url_pattern, text):
        return 'リンク省略'

    # それ以外の場合はURL部分のみを「リンク省略」に置き換える
    return re.sub(url_pattern, 'リンク省略', text)

# インテントを設定
intents = discord.Intents.default()
intents.message_content = True  # メッセージ内容を取得するために必要
intents.voice_states = True      # ボイスチャンネルの状態を取得するために必要
intents.members = True  # メンバー情報を取得するために必要

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print('Botが起動しました')

@bot.command(name="join")
async def join(ctx: commands.Context):
    # ユーザーがVCに接続しているか確認
    if ctx.author.voice is None:
        await ctx.send("あなたはボイスチャンネルに接続していません。")
        return
    
    # ボットをボイスチャンネルに接続
    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.send("ボイスチャンネルに接続しました！")

@bot.command(name="leave")
async def leave(ctx: commands.Context):
    # ボイスチャンネルからボットを切断
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()
        await ctx.send("ボイスチャンネルから切断しました。")
    else:
        await ctx.send("ボットはどのボイスチャンネルにも接続していません。")

@bot.event
async def on_message(message: discord.Message):
    # ボット自身が送信したメッセージには反応しない
    if message.author.bot:
        return

    # メッセージ内のURLを処理（URLがあれば「リンク省略」に置き換え）
    processed_message = process_message(message.content)

    # ボットがボイスチャンネルに接続していれば、メッセージ内容を読み上げ
    if message.guild.voice_client and message.guild.voice_client.is_connected():
        audio_data = talk(processed_message)  # URLが置き換えられたメッセージを音声合成
        with open("output.wav", "wb") as f:
            f.write(audio_data.read())

        # 音声ファイルを再生
        message.guild.voice_client.play(discord.FFmpegPCMAudio("output.wav"), after=lambda e: print("再生完了"))

    await bot.process_commands(message)  # コマンド処理も続けて行う


bot.run(TOKEN)
