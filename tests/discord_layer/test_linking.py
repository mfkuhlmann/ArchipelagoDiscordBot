from archibot.discord_layer.cogs.linking import LinkingCog
from tests.conftest import make_interaction


async def test_link_stores_caller_id(cogs_setup):
    bot, _, _ = cogs_setup
    cog = LinkingCog(bot)
    interaction = make_interaction(user_id=42, guild_id=10)
    await cog.link.callback(cog, interaction, slot="Meow")
    assert await bot.session_manager.slot_links.get(10, "Meow") == 42


async def test_link_updates_existing(cogs_setup):
    bot, _, _ = cogs_setup
    cog = LinkingCog(bot)
    await cog.link.callback(cog, make_interaction(user_id=42, guild_id=10), slot="Meow")
    await cog.link.callback(cog, make_interaction(user_id=99, guild_id=10), slot="Meow")
    assert await bot.session_manager.slot_links.get(10, "Meow") == 99


async def test_unlink_only_removes_caller_link(cogs_setup):
    bot, _, _ = cogs_setup
    cog = LinkingCog(bot)
    await cog.link.callback(cog, make_interaction(user_id=42, guild_id=10), slot="Meow")
    await cog.unlink.callback(cog, make_interaction(user_id=99, guild_id=10), slot="Meow")
    assert await bot.session_manager.slot_links.get(10, "Meow") == 42


async def test_unlink_no_slot_removes_all_for_user(cogs_setup):
    bot, _, _ = cogs_setup
    cog = LinkingCog(bot)
    await cog.link.callback(cog, make_interaction(user_id=42, guild_id=10), slot="Meow")
    await cog.link.callback(cog, make_interaction(user_id=42, guild_id=10), slot="Bork")
    await cog.unlink.callback(cog, make_interaction(user_id=42, guild_id=10), slot=None)
    assert await bot.session_manager.slot_links.get(10, "Meow") is None
    assert await bot.session_manager.slot_links.get(10, "Bork") is None


async def test_links_lists_guild_mappings(cogs_setup):
    bot, _, _ = cogs_setup
    cog = LinkingCog(bot)
    await cog.link.callback(cog, make_interaction(user_id=42, guild_id=10), slot="Meow")
    await cog.link.callback(cog, make_interaction(user_id=99, guild_id=10), slot="Bork")
    interaction = make_interaction(guild_id=10)
    await cog.links.callback(cog, interaction)
    message = interaction.response.send_message.await_args.args[0]
    assert "Meow" in message and "Bork" in message


async def test_players_reflect_link_and_mute_state(cogs_setup):
    bot, _, _ = cogs_setup
    cog = LinkingCog(bot)
    await bot.session_manager.track(
        channel_id=100,
        guild_id=10,
        host="localhost",
        port=38281,
        slot_name="Meow",
    )
    await bot.session_manager.slot_links.upsert(10, "Meow", 42)
    await bot.session_manager.muted_slots.mute(100, "Bork")
    interaction = make_interaction(guild_id=10)
    await cog.players.callback(cog, interaction)
    content = interaction.response.send_message.await_args.args[0]
    assert "[linked] `Meow`" in content
    assert "[muted] `Bork`" in content
