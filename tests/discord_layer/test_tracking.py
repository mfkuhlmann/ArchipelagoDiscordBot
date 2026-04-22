from archibot.discord_layer.cogs.tracking import TrackingCog
from archibot.persistence.crypto import CryptoUnavailableError
from tests.conftest import make_interaction


async def test_track_rejects_non_moderator(cogs_setup):
    bot, _, _ = cogs_setup
    cog = TrackingCog(bot)
    interaction = make_interaction(is_mod=False)
    await cog.track.callback(cog, interaction, "localhost", 38281, "Meow", "")
    assert not bot.session_manager.has_session(100)


async def test_track_starts_session(cogs_setup):
    bot, _, _ = cogs_setup
    cog = TrackingCog(bot)
    interaction = make_interaction()
    await cog.track.callback(cog, interaction, "localhost", 38281, "Meow", "")
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


async def test_track_handles_crypto_error(cogs_setup):
    bot, _, _ = cogs_setup

    async def boom(**_kwargs):
        raise CryptoUnavailableError("missing")

    bot.session_manager.track = boom
    cog = TrackingCog(bot)
    interaction = make_interaction()
    await cog.track.callback(cog, interaction, "localhost", 38281, "Meow", "secret")
    assert interaction.response.send_message.await_args.kwargs["ephemeral"] is True
