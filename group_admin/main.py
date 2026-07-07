from nonebot import on_command, CommandGroup
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.permission import SUPERUSER

__plugin_meta__ = PluginMetadata(
    name="group_admin",
    description="群管理插件",
    usage="",
)

group_admin_cmd = CommandGroup("group_admin", permission=SUPERUSER)

def is_group_admin(bot: Bot, event: GroupMessageEvent) -> bool:
    from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
    from nonebot.permission import check_permission
    
    async def _check():
        return await check_permission(bot, event, GROUP_ADMIN | GROUP_OWNER | SUPERUSER)
    
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_check())

async def get_group_admin_list(bot: Bot, group_id: int):
    members = await bot.get_group_member_list(group_id=group_id)
    admins = []
    for member in members:
        if member.get("role") in ("admin", "owner"):
            admins.append({
                "user_id": member["user_id"],
                "nickname": member.get("nickname", ""),
                "card": member.get("card", ""),
                "role": member["role"]
            })
    return admins

async def check_admin_permission(bot: Bot, event: MessageEvent, cmd):
    if not isinstance(event, GroupMessageEvent):
        await cmd.finish("此命令只能在群聊中使用！")
        return False
    
    user_id = event.user_id
    group_id = event.group_id
    
    bot_member_info = await bot.get_group_member_info(group_id=group_id, user_id=event.self_id)
    bot_role = bot_member_info.get("role")
    if bot_role not in ("admin", "owner"):
        await cmd.finish("❌ 暂无权限，无法使用管理菜单！\n请给予机器人管理员或群主权限后再试。")
        return False
    
    member_info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
    role = member_info.get("role")
    if role not in ("admin", "owner"):
        await cmd.finish("❌ 无权限操作此菜单！\n请联系群主或管理员获取权限后再试。")
        return False
    
    return True

group_admin_menu = on_command("群管理菜单", aliases={"群管"}, priority=2)

@group_admin_menu.handle()
async def handle_group_admin_menu(bot: Bot, event: MessageEvent):
    if not await check_admin_permission(bot, event, group_admin_menu):
        return
    
    menu = """🛠️ 群管理菜单
━━━━━━━━━━━━━━━━━
👤 成员管理：
  /踢人 <QQ号> [原因]
  /封禁 <QQ号> [原因]
  /解封 <QQ号>
  /禁言 <QQ号> [时长分钟]
  /解除禁言 <QQ号>
  /全员禁言
  /解除全员禁言

🏷️ 身份管理：
  /设管理员 <QQ号>
  /取消管理员 <QQ号>
  /改名片 <QQ号> <新名片>
  /专属头衔 <QQ号> <头衔>

📝 群设置：
  /改群名 <新群名>
  /群备注 <备注>
  /加群方式 <允许/拒绝/需验证>
  /群搜索 <开启/关闭>

📊 查询信息：
  /群信息
  /成员列表
  /成员信息 <QQ号>

💡 提示：所有命令只有管理员可用
💡 输入 /群管理菜单 或 /群管 查看此菜单"""
    
    await group_admin_menu.finish(menu)

kick_member = on_command("踢人", aliases={"踢出"}, priority=2)

@kick_member.handle()
async def handle_kick_member(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not await check_admin_permission(bot, event, kick_member):
        return
    
    arg_str = str(args).strip()
    if not arg_str:
        await kick_member.finish("请输入要踢出的QQ号，例如：/踢人 123456789")
        return
    
    parts = arg_str.split(" ", 1)
    target_id = parts[0].strip()
    reason = parts[1].strip() if len(parts) > 1 else "违规操作"
    
    if not target_id.isdigit():
        await kick_member.finish("QQ号格式不正确！")
        return
    
    try:
        await bot.set_group_kick(group_id=event.group_id, user_id=int(target_id), reject_add_request=False)
        await kick_member.finish(f"✅ 已成功踢出 QQ:{target_id}\n原因：{reason}")
    except Exception as e:
        await kick_member.finish(f"❌ 踢出失败：{str(e)}")

ban_member = on_command("封禁", aliases={"拉黑"}, priority=2)

@ban_member.handle()
async def handle_ban_member(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not await check_admin_permission(bot, event, ban_member):
        return
    
    arg_str = str(args).strip()
    if not arg_str:
        await ban_member.finish("请输入要封禁的QQ号，例如：/封禁 123456789")
        return
    
    parts = arg_str.split(" ", 1)
    target_id = parts[0].strip()
    reason = parts[1].strip() if len(parts) > 1 else "违规操作"
    
    if not target_id.isdigit():
        await ban_member.finish("QQ号格式不正确！")
        return
    
    try:
        await bot.set_group_kick(group_id=event.group_id, user_id=int(target_id), reject_add_request=True)
        await ban_member.finish(f"✅ 已成功封禁 QQ:{target_id}\n原因：{reason}\n该用户将无法再次加入本群")
    except Exception as e:
        await ban_member.finish(f"❌ 封禁失败：{str(e)}")

unban_member = on_command("解封", aliases={"解除封禁"}, priority=2)

@unban_member.handle()
async def handle_unban_member(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not await check_admin_permission(bot, event, unban_member):
        return
    
    arg_str = str(args).strip()
    if not arg_str:
        await unban_member.finish("请输入要解封的QQ号，例如：/解封 123456789")
        return
    
    if not arg_str.isdigit():
        await unban_member.finish("QQ号格式不正确！")
        return
    
    try:
        await bot.set_group_ban(group_id=event.group_id, user_id=int(arg_str), duration=0)
        await unban_member.finish(f"✅ 已成功解封 QQ:{arg_str}")
    except Exception as e:
        await unban_member.finish(f"❌ 解封失败：{str(e)}")

mute_member = on_command("禁言", priority=2)

@mute_member.handle()
async def handle_mute_member(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not await check_admin_permission(bot, event, mute_member):
        return
    
    arg_str = str(args).strip()
    if not arg_str:
        await mute_member.finish("请输入要禁言的QQ号和时长，例如：/禁言 123456789 60")
        return
    
    parts = arg_str.split(" ", 1)
    target_id = parts[0].strip()
    
    if not target_id.isdigit():
        await mute_member.finish("QQ号格式不正确！")
        return
    
    duration = 60
    if len(parts) > 1:
        try:
            duration = int(parts[1].strip())
        except ValueError:
            duration = 60
    
    try:
        await bot.set_group_ban(group_id=event.group_id, user_id=int(target_id), duration=duration * 60)
        await mute_member.finish(f"✅ 已成功禁言 QQ:{target_id} {duration}分钟")
    except Exception as e:
        await mute_member.finish(f"❌ 禁言失败：{str(e)}")

unmute_member = on_command("解除禁言", aliases={"解禁"}, priority=2)

@unmute_member.handle()
async def handle_unmute_member(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not await check_admin_permission(bot, event, unmute_member):
        return
    
    arg_str = str(args).strip()
    if not arg_str:
        await unmute_member.finish("请输入要解除禁言的QQ号，例如：/解除禁言 123456789")
        return
    
    if not arg_str.isdigit():
        await unmute_member.finish("QQ号格式不正确！")
        return
    
    try:
        await bot.set_group_ban(group_id=event.group_id, user_id=int(arg_str), duration=0)
        await unmute_member.finish(f"✅ 已成功解除禁言 QQ:{arg_str}")
    except Exception as e:
        await unmute_member.finish(f"❌ 解除禁言失败：{str(e)}")

mute_all = on_command("全员禁言", priority=2)

@mute_all.handle()
async def handle_mute_all(bot: Bot, event: MessageEvent):
    if not await check_admin_permission(bot, event, mute_all):
        return
    
    try:
        await bot.set_group_whole_ban(group_id=event.group_id, enable=True)
        await mute_all.finish("✅ 已开启全员禁言")
    except Exception as e:
        await mute_all.finish(f"❌ 开启全员禁言失败：{str(e)}")

unmute_all = on_command("解除全员禁言", aliases={"全员解禁"}, priority=2)

@unmute_all.handle()
async def handle_unmute_all(bot: Bot, event: MessageEvent):
    if not await check_admin_permission(bot, event, unmute_all):
        return
    
    try:
        await bot.set_group_whole_ban(group_id=event.group_id, enable=False)
        await unmute_all.finish("✅ 已解除全员禁言")
    except Exception as e:
        await unmute_all.finish(f"❌ 解除全员禁言失败：{str(e)}")

set_group_name = on_command("改群名", aliases={"修改群名", "群名"}, priority=2)

@set_group_name.handle()
async def handle_set_group_name(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not await check_admin_permission(bot, event, set_group_name):
        return
    
    name = str(args).strip()
    if not name:
        await set_group_name.finish("请输入新群名，例如：/改群名 我的新群")
        return
    
    try:
        await bot.set_group_name(group_id=event.group_id, group_name=name)
        await set_group_name.finish(f"✅ 群名已修改为：{name}")
    except Exception as e:
        await set_group_name.finish(f"❌ 修改群名失败：{str(e)}")

set_member_card = on_command("改名片", aliases={"修改名片", "名片"}, priority=2)

@set_member_card.handle()
async def handle_set_member_card(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not await check_admin_permission(bot, event, set_member_card):
        return
    
    arg_str = str(args).strip()
    if not arg_str:
        await set_member_card.finish("请输入QQ号和新名片，例如：/改名片 123456789 张三")
        return
    
    parts = arg_str.split(" ", 1)
    target_id = parts[0].strip()
    
    if not target_id.isdigit():
        await set_member_card.finish("QQ号格式不正确！")
        return
    
    card = parts[1].strip() if len(parts) > 1 else ""
    
    try:
        await bot.set_group_card(group_id=event.group_id, user_id=int(target_id), card=card)
        await set_member_card.finish(f"✅ 已修改 QQ:{target_id} 的群名片为：{card if card else '（重置为昵称）'}")
    except Exception as e:
        await set_member_card.finish(f"❌ 修改名片失败：{str(e)}")

set_member_special_title = on_command("专属头衔", priority=2)

@set_member_special_title.handle()
async def handle_set_member_special_title(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not await check_admin_permission(bot, event, set_member_special_title):
        return
    
    arg_str = str(args).strip()
    if not arg_str:
        await set_member_special_title.finish("请输入QQ号和专属头衔，例如：/专属头衔 123456789 管理员")
        return
    
    parts = arg_str.split(" ", 1)
    target_id = parts[0].strip()
    
    if not target_id.isdigit():
        await set_member_special_title.finish("QQ号格式不正确！")
        return
    
    title = parts[1].strip() if len(parts) > 1 else ""
    
    try:
        await bot.set_group_special_title(group_id=event.group_id, user_id=int(target_id), special_title=title)
        await set_member_special_title.finish(f"✅ 已设置 QQ:{target_id} 的专属头衔为：{title if title else '（移除头衔）'}")
    except Exception as e:
        await set_member_special_title.finish(f"❌ 设置头衔失败：{str(e)}")

set_group_admin = on_command("设管理员", aliases={"设置管理员"}, priority=2)

@set_group_admin.handle()
async def handle_set_group_admin(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not await check_admin_permission(bot, event, set_group_admin):
        return
    
    arg_str = str(args).strip()
    if not arg_str:
        await set_group_admin.finish("请输入要设为管理员的QQ号，例如：/设管理员 123456789")
        return
    
    if not arg_str.isdigit():
        await set_group_admin.finish("QQ号格式不正确！")
        return
    
    try:
        await bot.set_group_admin(group_id=event.group_id, user_id=int(arg_str), enable=True)
        await set_group_admin.finish(f"✅ 已设置 QQ:{arg_str} 为管理员")
    except Exception as e:
        await set_group_admin.finish(f"❌ 设置管理员失败：{str(e)}")

unset_group_admin = on_command("取消管理员", aliases={"移除管理员"}, priority=2)

@unset_group_admin.handle()
async def handle_unset_group_admin(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not await check_admin_permission(bot, event, unset_group_admin):
        return
    
    arg_str = str(args).strip()
    if not arg_str:
        await unset_group_admin.finish("请输入要取消管理员的QQ号，例如：/取消管理员 123456789")
        return
    
    if not arg_str.isdigit():
        await unset_group_admin.finish("QQ号格式不正确！")
        return
    
    try:
        await bot.set_group_admin(group_id=event.group_id, user_id=int(arg_str), enable=False)
        await unset_group_admin.finish(f"✅ 已取消 QQ:{arg_str} 的管理员权限")
    except Exception as e:
        await unset_group_admin.finish(f"❌ 取消管理员失败：{str(e)}")

set_group_remark = on_command("群备注", aliases={"修改群备注"}, priority=2)

@set_group_remark.handle()
async def handle_set_group_remark(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not await check_admin_permission(bot, event, set_group_remark):
        return
    
    remark = str(args).strip()
    
    try:
        await bot.set_group_remark(group_id=event.group_id, remark=remark)
        await set_group_remark.finish(f"✅ 群备注已修改为：{remark if remark else '（清空备注）'}")
    except Exception as e:
        await set_group_remark.finish(f"❌ 修改群备注失败：{str(e)}")

set_group_add_option = on_command("加群方式", aliases={"入群方式"}, priority=2)

@set_group_add_option.handle()
async def handle_set_group_add_option(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not await check_admin_permission(bot, event, set_group_add_option):
        return
    
    arg_str = str(args).strip()
    if not arg_str:
        await set_group_add_option.finish("请输入加群方式：允许/拒绝/需验证，例如：/加群方式 需验证")
        return
    
    option_map = {
        "允许": "allow",
        "拒绝": "deny",
        "需验证": "need_confirm"
    }
    
    option = option_map.get(arg_str, "")
    if not option:
        await set_group_add_option.finish("无效的加群方式！请输入：允许/拒绝/需验证")
        return
    
    try:
        await bot.set_group_add_request(group_id=event.group_id, approve=True, reason="")
        await bot.set_group_add_option(group_id=event.group_id, add_option=option)
        await set_group_add_option.finish(f"✅ 加群方式已设置为：{arg_str}")
    except Exception as e:
        await set_group_add_option.finish(f"❌ 设置加群方式失败：{str(e)}")

set_group_search = on_command("群搜索", aliases={"搜索设置"}, priority=2)

@set_group_search.handle()
async def handle_set_group_search(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not await check_admin_permission(bot, event, set_group_search):
        return
    
    arg_str = str(args).strip()
    if not arg_str:
        await set_group_search.finish("请输入群搜索设置：开启/关闭，例如：/群搜索 关闭")
        return
    
    if arg_str not in ("开启", "关闭"):
        await set_group_search.finish("无效的设置！请输入：开启/关闭")
        return
    
    try:
        await bot.set_group_searchable(group_id=event.group_id, enable=(arg_str == "开启"))
        await set_group_search.finish(f"✅ 群搜索已{arg_str}")
    except Exception as e:
        await set_group_search.finish(f"❌ 设置群搜索失败：{str(e)}")

get_group_info = on_command("群信息", aliases={"查看群信息"}, priority=2)

@get_group_info.handle()
async def handle_get_group_info(bot: Bot, event: MessageEvent):
    if not await check_admin_permission(bot, event, get_group_info):
        return
    
    try:
        info = await bot.get_group_info(group_id=event.group_id)
        
        result = f"""📊 群信息
━━━━━━━━━━━━━━━━━
群号：{info.get('group_id', '')}
群名：{info.get('group_name', '')}
成员数：{info.get('member_count', '')}
最大成员数：{info.get('max_member_count', '')}
群主：{info.get('owner_id', '')}
创建时间：{info.get('create_time', '')}
公告：{info.get('group_memo', '无')}"""
        
        await get_group_info.finish(result)
    except Exception as e:
        await get_group_info.finish(f"❌ 获取群信息失败：{str(e)}")

get_group_member_list = on_command("成员列表", aliases={"群成员"}, priority=2)

@get_group_member_list.handle()
async def handle_get_group_member_list(bot: Bot, event: MessageEvent):
    if not await check_admin_permission(bot, event, get_group_member_list):
        return
    
    try:
        members = await bot.get_group_member_list(group_id=event.group_id)
        
        owners = []
        admins = []
        normal = []
        
        for member in members:
            user_id = member.get("user_id", "")
            nickname = member.get("nickname", "")
            card = member.get("card", "") or nickname
            role = member.get("role", "member")
            
            if role == "owner":
                owners.append(f"👑 {card} ({user_id})")
            elif role == "admin":
                admins.append(f"🔧 {card} ({user_id})")
            else:
                normal.append(f"👤 {card} ({user_id})")
        
        result = f"""👥 群成员列表
━━━━━━━━━━━━━━━━━
群主：{len(owners)}人
{chr(10).join(owners) if owners else '无'}

管理员：{len(admins)}人
{chr(10).join(admins) if admins else '无'}

普通成员：{len(normal)}人
{chr(10).join(normal[:20]) if normal else '无'}
{chr(10) + f'... 还有 {len(normal) - 20} 人未显示' if len(normal) > 20 else ''}

总计：{len(members)}人"""
        
        await get_group_member_list.finish(result)
    except Exception as e:
        await get_group_member_list.finish(f"❌ 获取成员列表失败：{str(e)}")

get_member_info = on_command("成员信息", aliases={"查看成员"}, priority=2)

@get_member_info.handle()
async def handle_get_member_info(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    if not await check_admin_permission(bot, event, get_member_info):
        return
    
    arg_str = str(args).strip()
    if not arg_str:
        await get_member_info.finish("请输入要查询的QQ号，例如：/成员信息 123456789")
        return
    
    if not arg_str.isdigit():
        await get_member_info.finish("QQ号格式不正确！")
        return
    
    try:
        info = await bot.get_group_member_info(group_id=event.group_id, user_id=int(arg_str))
        
        role_map = {
            "owner": "群主",
            "admin": "管理员",
            "member": "普通成员"
        }
        
        result = f"""👤 成员信息
━━━━━━━━━━━━━━━━━
QQ号：{info.get('user_id', '')}
昵称：{info.get('nickname', '')}
群名片：{info.get('card', '无')}
专属头衔：{info.get('special_title', '无')}
身份：{role_map.get(info.get('role', ''), '未知')}
入群时间：{info.get('join_time', '未知')}
发言次数：{info.get('message_count', '未知')}
禁言状态：{'🔕 已禁言' if info.get('shut_up_timestamp', 0) > 0 else '🗣️ 正常'}"""
        
        await get_member_info.finish(result)
    except Exception as e:
        await get_member_info.finish(f"❌ 获取成员信息失败：{str(e)}")

group_admin_help = on_command("群管帮助", priority=2)

@group_admin_help.handle()
async def handle_group_admin_help(bot: Bot, event: MessageEvent):
    if not await check_admin_permission(bot, event, group_admin_help):
        return
    
    help_text = """🛠️ 群管理命令帮助
━━━━━━━━━━━━━━━━━

👤 成员管理：
  /踢人 <QQ号> [原因]       - 踢出群成员
  /封禁 <QQ号> [原因]       - 踢出并拉黑
  /解封 <QQ号>             - 解除封禁
  /禁言 <QQ号> [分钟]       - 禁言成员（默认60分钟）
  /解除禁言 <QQ号>         - 解除禁言
  /全员禁言                 - 开启全员禁言
  /解除全员禁言             - 关闭全员禁言

🏷️ 身份管理：
  /设管理员 <QQ号>          - 设置管理员
  /取消管理员 <QQ号>        - 取消管理员
  /改名片 <QQ号> <新名片>   - 修改群名片
  /专属头衔 <QQ号> <头衔>   - 设置专属头衔

📝 群设置：
  /改群名 <新群名>          - 修改群名称
  /群备注 <备注>            - 修改群备注
  /加群方式 <允许/拒绝/需验证> - 设置加群方式
  /群搜索 <开启/关闭>       - 设置群可搜索

📊 查询信息：
  /群信息                   - 查看群详细信息
  /成员列表                 - 查看群成员列表
  /成员信息 <QQ号>          - 查看成员详细信息

💡 提示：所有命令只有管理员和群主可以使用"""
    
    await group_admin_help.finish(help_text)



