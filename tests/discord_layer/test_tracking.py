from archibot.discord_layer.cogs.tracking import TrackingCog
from archibot.persistence.crypto import CryptoUnavailableError
from tests.conftest import make_interaction


async def test_track_rejects_non_moderator(cogs_setup):
    bot, _, _ = cogs_setup
    cog = TrackingCog(bot)
    interaction = make_interaction(is_mod=False)
    await cog.track.callback(cog, interaction, "localhost", 38281, "Meow", "embed", "")
    assert not bot.session_manager.has_session(100)


async def test_track_starts_session(cogs_setup):
    bot, _, _ = cogs_setup
    cog = TrackingCog(bot)
    interaction = make_interaction()
    await cog.track.callback(cog, interaction, "localhost", 38281, "Meow", "embed", "")
    assert bot.session_manager.has_session(100)


async def test_status_returns_embed(cogs_setup):
    bot, _, _ = cogs_setup
    cog = TrackingCog(bot)
    interaction = make_interaction()
    await cog.status.callback(cog, interaction)
    assert interaction.response.send_message.await_count == 1
    assert (
        interaction.response.send_message.await_args.kwargs["embed"].title
        == "Archipelago Tracker Status"
    )


async def test_raspberry_returns_embed(cogs_setup):
    bot, _, _ = cogs_setup
    cog = TrackingCog(bot)
    await bot.session_manager.raspberry_counts.increment(100, "Meow")
    await bot.session_manager.raspberry_counts.increment(100, "Meow")
    await bot.session_manager.raspberry_counts.increment(100, "Bork")
    interaction = make_interaction()
    await cog.raspberry.callback(cog, interaction)
    embed = interaction.response.send_message.await_args.kwargs["embed"]
    assert embed.title == "Raspberry Counter"
    assert embed.fields[0].value == "3"
    assert "Meow: 2" in embed.fields[1].value
    assert "Bork: 1" in embed.fields[1].value


async def test_track_handles_crypto_error(cogs_setup):
    bot, _, _ = cogs_setup

    async def boom(**_kwargs):
        raise CryptoUnavailableError("missing")

    bot.session_manager.track = boom
    cog = TrackingCog(bot)
    interaction = make_interaction()
    await cog.track.callback(cog, interaction, "localhost", 38281, "Meow", "embed", "secret")
    assert interaction.response.send_message.await_args.kwargs["ephemeral"] is True


async def test_track_persists_plain_message_style(cogs_setup):
    bot, _, _ = cogs_setup
    cog = TrackingCog(bot)
    interaction = make_interaction()
    await cog.track.callback(cog, interaction, "localhost", 38281, "Meow", "plain", "")
    record, _ = await bot.session_manager.sessions.get(100)
    assert record.message_style == "plain"
