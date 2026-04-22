from archibot.discord_layer.cogs.moderation import ModerationCog
from tests.conftest import make_interaction


async def test_mute_requires_mod_role(cogs_setup):
    bot, _, _ = cogs_setup
    cog = ModerationCog(bot)
    interaction = make_interaction(is_mod=False)
    await cog.mute.callback(cog, interaction, slot="Meow")
    assert not await bot.session_manager.muted_slots.is_muted(100, "Meow")


async def test_mute_persists(cogs_setup):
    bot, _, _ = cogs_setup
    cog = ModerationCog(bot)
    await cog.mute.callback(cog, make_interaction(), slot="Meow")
    assert await bot.session_manager.muted_slots.is_muted(100, "Meow")


async def test_unmute_persists(cogs_setup):
    bot, _, _ = cogs_setup
    cog = ModerationCog(bot)
    await cog.mute.callback(cog, make_interaction(), slot="Meow")
    await cog.unmute.callback(cog, make_interaction(), slot="Meow")
    assert not await bot.session_manager.muted_slots.is_muted(100, "Meow")
