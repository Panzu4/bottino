# LIBRERIE python.exe -m pip install --upgrade per aggiornamenti
import asyncio
import datetime
import json
import os
import random
import sys
import webbrowser
import concurrent.futures
import aiohttp
import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import Embed
import yt_dlp as youtube_dl
from packaging.version import parse as parse_version

# CONFIGURATION
def load_token():
    if os.path.exists('token.txt'):
        with open('token.txt', 'r') as f:
            return f.read().strip()
    else:
        # Se il file non esiste, lo crea vuoto per l'utente
        with open('token.txt', 'w') as f:
            f.write("INCOLLA_QUI_IL_TUO_TOKEN")
        print("File 'token.txt' creato. Incolla il tuo token e riavvia.")
        return None

TOKEN = load_token()
COMMAND_PREFIX = '!'
BOT_VERSION = "2.1.5"
LATEST_VERSION_URL = "https://gist.githubusercontent.com/Panzu4/d75cdbf636177b8b5000fb14d65e1bab/raw"
RELEASE_URL = "https://github.com/Panzu4/bottino/releases"
STATE_FILE = 'bot_state.json'

# YTDL AND FFMPEG SETTINGS
ytdl_format_options = {
    'format': 'bestaudio[ext=opus][abr<=32]/bestaudio[abr<=32]/bestaudio[ext=opus][abr<=64]/bestaudio[abr<=64]/bestaudio',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': False,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -f wav'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# UTILITY CLASSES
class YTDLSource(discord.PCMVolumeTransformer):
    """Rappresenta una sorgente audio riproducibile da YouTube."""
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.original_url = data.get('webpage_url')
        self.thumbnail = data.get('thumbnail')
        self.duration = data.get('duration')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, pre_fetched_data=None, executor=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(executor, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data and data.get('_type') == 'playlist':
            data = data['entries'][0] if data['entries'] else None

        if data is None:
            raise Exception("Nessun dato video valido trovato.")

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# UI DISCORD
class HelpMenu(View):
    def __init__(self, ctx):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.current_page = 1

    async def update_embed(self, interaction):
        embed = self.get_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    def get_embed(self):
        if self.current_page == 1:
            embed = Embed(title="Comandi Essenziali", color=0xFF00FF)
            embed.add_field(name="!play", value="Avvia la riproduzione di un brano o di una playlist. Accetta sia link che termini di ricerca. I video privati/non disponibili verranno saltati.", inline=False)
            embed.add_field(name="!skip", value="I wander what this does 🤔", inline=False)
            embed.add_field(name="!suca", value="Mi faceva piu ridere di !stop (puoi usare anche !stop)", inline=False)
            embed.add_field(name="!queue", value="Vedi che merda hai messo in coda (ora con pagine!)", inline=False)
            embed.add_field(name="!loop", value="Per le canzoni di Checco", inline=False)
            embed.add_field(name="!remove", value="Esattamente quello che stai pensando, non dimenticarti di mettere il numero di quale posizione vuoi rimuovere dalla coda", inline=False)
            embed.add_field(name="!hints", value="Grande gioco del sium GIOCATELO ORA", inline=False)
            embed.add_field(name="!H", value="👍", inline=False)
            embed.set_footer(text=f"Pagina {self.current_page}/3")
        elif self.current_page == 2:
            embed = Embed(title="Comandi Secondari", color=0xFF00FF)
            embed.add_field(name="!join", value="Comando onestamente inutile, ma serve per le altre funzioni", inline=False)
            embed.add_field(name="!next", value="Se hai bisogno di mettere qualcosa come primo in lista", inline=False)
            embed.add_field(name="!shuffle", value="Lo aveva spotify, perche non io?", inline=False)
            embed.add_field(name="!addto", value="Se !next ti fa schifo puoi scrivere !addto 1 Caparezza - La Scelta", inline=False)
            embed.add_field(name="!move", value="Boh ho finito le frasi divertenti, Si usa scrivendo !move 1 to 2 se vuoi scambiare le posizioni (non sessuali)", inline=False)
            embed.add_field(name="!jump", value="Salta direttamente a una canzone nella coda senza eliminarle! Es: !jump 3", inline=False)
            embed.add_field(name="!muvt", value="Serve per quando il coglione si blocca", inline=False)
            embed.add_field(name="!ping", value="Controlla la latenza del bot.", inline=False)
            embed.add_field(name="!close", value="Chiude il bot", inline=False)
            embed.add_field(name="!🥚", value="E G G", inline=False)
            embed.set_footer(text=f"Pagina {self.current_page}/3")
        elif self.current_page == 3:
            embed = Embed(title="Versione 2.1.4", color=0xFF00FF)
            embed.set_footer(text=f"Pagina {self.current_page}/3")
            embed.set_image(url="https://media.tenor.com/y3fmODUSLpIAAAAm/tenna-deltarune-chapter-3.webp")
        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 1:
            self.current_page -= 1
        else:
            self.current_page = 3
        await self.update_embed(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        if self.current_page < 3:
            self.current_page += 1
        else:
            self.current_page = 1
        await self.update_embed(interaction)

class PlaybackControls(View):
    def __init__(self, ctx, progress_message, elapsed_time, total_duration, bot_queues, bot_looping, bot_paused_state):
        super().__init__(timeout= total_duration + 120)
        self.ctx = ctx
        self.progress_message = progress_message
        self.elapsed_time = elapsed_time 
        self.total_duration = total_duration
        self.paused = False
        self.pause_time = None
        self.start_time = datetime.datetime.now() - datetime.timedelta(seconds=elapsed_time) 
        self.bot_queues = bot_queues
        self.bot_looping = bot_looping
        self.bot_paused_state = bot_paused_state

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.primary)
    async def pause_resume(self, interaction: discord.Interaction, button: Button):
        guild_id = self.ctx.guild.id 

        if not self.ctx.voice_client:
            await interaction.response.send_message("Non sto riproducendo nulla al momento!", ephemeral=False)
            return

        if not self.paused:
            self.elapsed_time = (datetime.datetime.now() - self.start_time).total_seconds()
            self.ctx.voice_client.pause()
            self.paused = True
            self.pause_time = datetime.datetime.now()
            self.bot_paused_state[guild_id] = True
            button.label = "Resume"
            await interaction.response.edit_message(view=self)
        else:
            self.start_time = datetime.datetime.now() - datetime.timedelta(seconds=self.elapsed_time)
            self.ctx.voice_client.resume()
            self.paused = False
            self.pause_time = None
            self.bot_paused_state[guild_id] = False
            button.label = "Pause"
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Loop", style=discord.ButtonStyle.primary)
    async def loop_button(self, interaction: discord.Interaction, button: Button):
        guild_id = self.ctx.guild.id
        if guild_id in self.bot_looping and self.bot_looping[guild_id]:
            self.bot_looping[guild_id] = False
            if self.bot_queues[guild_id]:
                if self.bot_queues[guild_id][0].get('is_loop_item'):
                    self.bot.queues[guild_id].pop(0)
            await interaction.response.send_message("Loop 👎", ephemeral=False)
        else:
            self.bot_looping[guild_id] = True
            current_source = self.ctx.voice_client.source
            if isinstance(current_source, YTDLSource):
                current_song = {'title': current_source.title, 'url': current_source.url, 'is_loop_item': True}
                self.bot_queues[guild_id].insert(0, current_song)
                await interaction.response.send_message(f"Loop 👍", ephemeral=False)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.danger)
    async def skip_button(self, interaction: discord.Interaction, button: Button):
        if not self.ctx.voice_client or not self.ctx.voice_client.is_playing():
            await interaction.response.send_message("Fratello in cristo che minchia stai cercando di skippare", ephemeral=True)
            return
        self.ctx.voice_client.stop()
        await interaction.response.send_message("⏩ Song skipped ⏩", ephemeral=False)

    @discord.ui.button(label="Suca", style=discord.ButtonStyle.danger)
    async def suca_button(self, interaction: discord.Interaction, button: Button):
        if self.ctx.voice_client:
            self.bot_queues[self.ctx.guild.id] = []
            self.ctx.voice_client.stop()
            await interaction.response.send_message("Suca tu!", ephemeral=False)
        else:
            await interaction.response.send_message("Non c'è nulla da fermare! 🛑", ephemeral=True)

    @discord.ui.button(label="H 👍", style=discord.ButtonStyle.success)
    async def h_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("H 👍", ephemeral=False)

class QueueView(View):
    """View per la paginazione della coda musicale."""
    def __init__(self, bot_queues, guild_id, total_pages, initial_page=1, songs_per_page=15):
        super().__init__(timeout=180)
        self.bot_queues = bot_queues
        self.guild_id = guild_id
        self.total_pages = total_pages
        self.current_page = initial_page
        self.songs_per_page = songs_per_page

    async def update_embed(self, interaction: discord.Interaction):
        """Aggiorna l'embed del messaggio con la pagina corrente della coda."""
        embed = self.get_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    def get_embed(self):
        """Genera l'embed per la pagina corrente della coda."""
        queue = self.bot_queues.get(self.guild_id, [])
        if not queue:
            return Embed(title="Coda di Riproduzione", description="La coda è vuota.", color=0xFF00FF)

        start_index = (self.current_page - 1) * self.songs_per_page
        end_index = start_index + self.songs_per_page
        current_page_songs = queue[start_index:end_index]

        embed = Embed(title="Coda di Riproduzione", color=0xFF00FF)
        description = ""
        for i, item in enumerate(current_page_songs):
            description += f"{start_index + i + 1}. {item['title']}\n"
        
        embed.description = description
        embed.set_footer(text=f"Pagina {self.current_page}/{self.total_pages}")
        return embed

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary, custom_id="prev_queue_page")
    async def previous_page(self, interaction: discord.Interaction, button: Button):
        """Passa alla pagina precedente della coda."""
        self.current_page = (self.current_page - 2 + self.total_pages) % self.total_pages + 1
        await self.update_embed(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary, custom_id="next_queue_page")
    async def next_page(self, interaction: discord.Interaction, button: Button):
        """Passa alla pagina successiva della coda."""
        self.current_page = self.current_page % self.total_pages + 1
        await self.update_embed(interaction)

# PROGRESS BAR
async def update_progress_bar(ctx, progress_message, total_duration, controls):
    """Aggiorna la barra di avanzamento della riproduzione in un messaggio."""
    # Rimuovi la riga: start_playback_time = datetime.datetime.now() - datetime.timedelta(seconds=controls.elapsed_time)

    while ctx.voice_client and (ctx.voice_client.is_playing() or controls.paused):
        if controls.paused:
            current_elapsed = controls.elapsed_time # Usa il tempo trascorso salvato al momento della pausa
        else:
            current_elapsed = (datetime.datetime.now() - controls.start_time).total_seconds() # Calcola dal tempo di inizio aggiustato
            
        current_elapsed = min(current_elapsed, total_duration)

        progress = int((current_elapsed / total_duration) * 20)
        bar = "▬" * progress + "🤨" + "▬" * (20 - progress)
        elapsed_time_str = str(datetime.timedelta(seconds=int(current_elapsed)))
        total_time_str = str(datetime.timedelta(seconds=total_duration))

        embed = progress_message.embeds[0]
        embed.description = f"`[{elapsed_time_str} {bar} {total_time_str}]`"
        await progress_message.edit(embed=embed)

        await asyncio.sleep(5)

    if progress_message and not controls.paused: # Aggiunto check per controls.paused per evitare che il messaggio cambi se si stoppa mentre è in pausa
        embed = progress_message.embeds[0]
        embed.description = "Appost 🗿👍"
        await progress_message.edit(embed=embed)

# CLASSES DI FUNZIONE

class Events(commands.Cog):
    """Gestisce gli eventi del bot come gli aggiornamenti dello stato vocale e i comandi generali."""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member == self.bot.user and after.channel is None:
            for guild_id in self.bot.queues:
                self.bot.queues[guild_id] = []
            for guild_id in self.bot.looping:
                self.bot.looping[guild_id] = False

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.command(name='ping')
    async def ping(self, ctx):
        latency = self.bot.latency * 1000
        await ctx.send(f"Latenza: {latency:.2f}ms")

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ydl = youtube_dl.YoutubeDL(ytdl_format_options)
        self.paused_state = {}

    async def play_next(self, ctx):
        """Riproduce la prossima canzone nella coda."""
        guild_id = ctx.guild.id

        if guild_id in self.bot.looping and self.bot.looping[guild_id] and self.bot.queues[guild_id]:
            await self.play_song(ctx, self.bot.queues[guild_id][0]['url'], is_loop=True)
        elif guild_id in self.bot.queues and self.bot.queues[guild_id]:
            next_song = self.bot.queues[guild_id].pop(0)
            await self.play_song(ctx, next_song['url'])
        else:
            if guild_id in self.bot.looping and self.bot.looping[guild_id]:
                self.bot.looping[guild_id] = False
                await ctx.send("Loop disattivato perché la coda è terminata.")

    async def play_song(self, ctx, url, is_loop=False):
        guild_id = ctx.guild.id
        def after_playing(error):
            if error:
                print(f"Errore durante la riproduzione: {error}")
            if not self.bot.paused_state.get(guild_id, False):
                self.bot.loop.create_task(self._after_playing_task(ctx))
        try:
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=after_playing)
            self.bot.paused_state[guild_id] = False
        except Exception as e:
            print(f"Error creating YTDLSource or playing: {e}")
            await ctx.send(f"Errore durante la riproduzione del brano: {e}")
            self.bot.loop.create_task(self.play_next(ctx))
            return
        if not is_loop:
            embed = discord.Embed(
                title=player.title,
                url=player.original_url,
                color=0xFF00FF
            )
            embed.set_image(url=player.thumbnail)

            channel_name = player.data.get('uploader', 'Canale sconosciuto')
            embed.add_field(name="Canale YouTube", value=channel_name, inline=False)
            embed.set_footer(text="Spero stia andando...")

            progress_message = await ctx.send(embed=embed)

            total_duration = player.duration or 0
            controls = PlaybackControls(ctx, progress_message, elapsed_time=0, total_duration=total_duration, bot_queues=self.bot.queues, bot_looping=self.bot.looping, bot_paused_state=self.bot.paused_state) # Pass the new state
            await progress_message.edit(view=controls)
            await update_progress_bar(ctx, progress_message, total_duration, controls)

    async def _after_playing_task(self, ctx):
        """Internal task to be called after a song finishes or is stopped."""
        await asyncio.sleep(0.1)
        await self.play_next(ctx)

    # --- Music Commands ---
    @commands.command(name='join')
    async def join(self, ctx):
        if not ctx.message.author.voice:
            await ctx.send(f"Entra nel canale prima pwease")
            return
        voice_channel = ctx.message.author.voice.channel
        try:
            await voice_channel.connect()
        except Exception as e:
            await ctx.send(f"Errore durante la connessione al canale vocale: {e}")
            print(f"Errore connessione: {e}") 

    @commands.command(name='leave')
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            guild_id = ctx.guild.id
            if guild_id in self.bot.queues:
                self.bot.queues[guild_id] = []
            if guild_id in self.bot.looping:
                self.bot.looping[guild_id] = False

    @commands.command(name='play', aliases=["Play"])
    async def play(self, ctx, *, search_term):
        if not ctx.voice_client:
            await self.join(ctx)

        guild_id = ctx.guild.id

        if ctx.guild.id not in self.bot.queues:
            self.bot.queues[ctx.guild.id] = []

        loading_message = await ctx.send("Let me cook 🍳...")

        try:
            is_playlist_url = "playlist?list=" in search_term or "/playlist/" in search_term

            ytdl_opts_for_playlist = {**ytdl_format_options}
            if is_playlist_url:
                ytdl_opts_for_playlist['extract_flat'] = 'webpage_url'
                ytdl_opts_for_playlist['noplaylist'] = False
            temp_ytdl = youtube_dl.YoutubeDL(ytdl_opts_for_playlist)

            raw_info = await self.bot.loop.run_in_executor(self.bot.executor, lambda: temp_ytdl.extract_info(search_term, download=False)) # Usato executor

            info_list = []
            if 'entries' in raw_info and raw_info.get('_type') in ['playlist', 'multi_video']:
                info_list = raw_info['entries']
            elif raw_info:
                info_list = [raw_info]
            
            if not info_list:
                await loading_message.edit(content="Errore inaspettato: nessun dato valido trovato o video non disponibile/privato.")
                print(f"DEBUG: No valid entries found in info_list for search_term: {search_term}")
                return

            added_songs = 0
            skipped_songs = 0
            
            if len(info_list) > 1:
                total_songs = len(info_list)
                await loading_message.edit(content=f"Sto caricando la playlist... 0% (Trovate {total_songs} tracce)")

            for index, entry in enumerate(info_list):
                if not isinstance(entry, dict):
                    print(f"DEBUG: Skipping non-dictionary entry: {entry}")
                    skipped_songs += 1
                    continue

                video_url = entry.get('webpage_url') or entry.get('url')
                video_title = entry.get('title')
                if video_url and video_title:
                    self.bot.queues[ctx.guild.id].append({'title': video_title, 'url': video_url})
                    added_songs += 1
                else:
                    skipped_songs += 1
                if len(info_list) > 1:
                    progress = int((index + 1) / total_songs * 100)
                    await loading_message.edit(content=f"Sto caricando la playlist... {progress}% ({added_songs} aggiunte, {skipped_songs} saltate)")

            if added_songs > 0:
                if len(info_list) > 1:
                    await loading_message.edit(content=f"Aggiunti {added_songs} brani alla coda. 🗿👍")
                else:
                    await loading_message.edit(content=f"Aggiunto alla coda: {info_list[0].get('title', 'Brano sconosciuto')} 🗿👍")
            else:
                await loading_message.edit(content="Nessun brano valido trovato o tutti i brani sono stati saltati.")

            if not (ctx.voice_client.is_playing() or self.bot.paused_state.get(guild_id, False)):
                await self.play_next(ctx)
        except Exception as e:
            await loading_message.edit(content=f"Errore durante il caricamento: {str(e)}")
            print(f"DEBUG: Exception in play command: {e}")

    @commands.command(name='queue', aliases=["coda"])
    async def queue(self, ctx, page: int = 1):
        guild_id = ctx.guild.id
        if guild_id not in self.bot.queues or not self.bot.queues[guild_id]:
            await ctx.send("Non c'è un cazzo qua")
            return

        songs_per_page = 15
        total_songs = len(self.bot.queues[guild_id])
        total_pages = (total_songs + songs_per_page - 1) // songs_per_page

        if not (1 <= page <= total_pages):
            await ctx.send(f"Pagina non valida. Ci sono {total_pages} pagine.")
            return

        view = QueueView(self.bot.queues, guild_id, total_pages, initial_page=page, songs_per_page=songs_per_page)
        embed = view.get_embed()
        await ctx.send(embed=embed, view=view)

    @commands.command(name='skip')
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏩ song skipped ⏩")
        else:
            await ctx.send('Quanta cattiveria i questa società')

    @commands.command(name='suca', aliases=["stop"])
    async def stop(self, ctx):
        if ctx.guild.id in self.bot.queues:
            self.bot.queues[ctx.guild.id] = []
        if ctx.guild.id in self.bot.looping:
            self.bot.looping[ctx.guild.id] = False
        if ctx.voice_client:
            ctx.voice_client.stop()
        await ctx.send("Suca tu")

    @commands.command(name='loop')
    async def loop(self, ctx):
        guild_id = ctx.guild.id

        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("Bro there is no shit to loop")
            return

        if guild_id not in self.bot.queues:
            self.bot.queues[guild_id] = []

        if guild_id in self.bot.looping and self.bot.looping[guild_id]:
            self.bot.looping[guild_id] = False
            if self.bot.queues[guild_id] and self.bot.queues[guild_id][0].get('is_loop_item'):
                self.bot.queues[guild_id].pop(0)
            await ctx.send("Loop 👎")
            return

        self.bot.looping[guild_id] = True
        current_source = ctx.voice_client.source
        if isinstance(current_source, YTDLSource):
            current_song = {
                'title': current_source.title,
                'url': current_source.url,
                'is_loop_item': True
            }
            self.bot.queues[guild_id].insert(0, current_song)
        else:
            await ctx.send("Errore nel recuperare la traccia in riproduzione.")
            self.bot.looping[guild_id] = False

        await ctx.send("Loop 👍")

    @commands.command(name='remove')
    async def remove(self, ctx, index: int = None):
        if index is None:
            await ctx.send("Non c’è un cazzo proprio")
            return

        if ctx.guild.id in self.bot.queues and 0 <= index - 1 < len(self.bot.queues[ctx.guild.id]):
            removed = self.bot.queues[ctx.guild.id].pop(index - 1)
            await ctx.send(f"Rimossa dalla coda: {removed['title']} 🗿👍")
        else:
            await ctx.send("Posizione non valida. (non intendo del sesso)")

    @commands.command(name='addto')
    async def addto(self, ctx, index: int = None, *, search_term=None):
        if index is None or search_term is None:
            await ctx.send("Non c’è un cazzo proprio")
            return

        if ctx.guild.id not in self.bot.queues:
            self.bot.queues[ctx.guild.id] = []

        loading_message = await ctx.send("Let me cook...")

        info = await self.bot.loop.run_in_executor(self.bot.executor, lambda: ytdl.extract_info(search_term, download=False)) 
        entry_to_add = None
        if 'entries' in info and len(info['entries']) > 0:
            valid_entries = [e for e in info['entries'] if e and not e.get('private') and not e.get('is_unavailable')]
            if valid_entries:
                entry_to_add = valid_entries[0]
            else:
                await loading_message.edit(content="Nessun video valido trovato nel risultato della ricerca/playlist.")
                return
        elif info and not info.get('private') and not info.get('is_unavailable'):
            entry_to_add = info
        else:
            await loading_message.edit(content="Il video non è disponibile o è privato, non può essere aggiunto.")
            return

        video_url = entry_to_add.get('webpage_url') or entry_to_add.get('url')
        title = entry_to_add.get('title')

        if video_url and title:
            if not (0 <= index - 1 <= len(self.bot.queues[ctx.guild.id])):
                index = len(self.bot.queues[ctx.guild.id]) + 1

            self.bot.queues[ctx.guild.id].insert(index - 1, {'title': title, 'url': video_url})
            await loading_message.edit(content=f"Aggiunto in posizione {index}: {title}")
        else:
            await loading_message.edit(content=f"Errore durante l'ottenimento delle informazioni del video.")

    @commands.command(name='next')
    async def next(self, ctx, *, search_term=None):
        if search_term is None:
            await ctx.send("Non c’è un cazzo proprio")
            return

        if not ctx.voice_client:
            await self.join(ctx)
        
        guild_id = ctx.guild.id

        if ctx.guild.id not in self.bot.queues:
            self.bot.queues[ctx.guild.id] = []
        loading_message = await ctx.send("Caricamento in corso...")
        try:
            info = await self.bot.loop.run_in_executor(self.bot.executor, lambda: ytdl.extract_info(search_term, download=False)) # Usato executor

            if 'entries' in info:
                added_count = 0
                for entry in reversed(info['entries']):
                    if entry and entry.get('webpage_url') and not entry.get('private') and not entry.get('is_unavailable'):
                        self.bot.queues[ctx.guild.id].insert(0, {'title': entry['title'], 'url': entry['webpage_url']})
                        added_count += 1
                    else:
                        print(f"Skipping private/unavailable song in !next: {entry.get('title', 'Unknown Title')}")
                if added_count > 0:
                    await loading_message.edit(content=f"Aggiunti {added_count} brani come prossimi in coda. 🗿👍")
                else:
                    await loading_message.edit(content="Nessun brano valido trovato da aggiungere come prossimo.")
            else:
                video_url = info['webpage_url']
                video_title = info['title']
                self.bot.queues[ctx.guild.id].insert(0, {'title': video_title, 'url': video_url})
                await loading_message.edit(content=f"Aggiunto come prossimo in coda: {video_title} 🗿👍")
            
            if not (ctx.voice_client.is_playing() or self.bot.paused_state.get(guild_id, False)):
                await self.play_next(ctx)

        except Exception as e:
            await ctx.send(f"E dio merda: {str(e)}")

    @commands.command(name='move')
    async def move(self, ctx, from_index: int = None, to_index: int = None):
        if from_index is None or to_index is None:
            await ctx.send("Non c’è un cazzo proprio")
            return

        if ctx.guild.id in self.bot.queues and 0 <= from_index - 1 < len(self.bot.queues[ctx.guild.id]):
            song = self.bot.queues[ctx.guild.id].pop(from_index - 1)
            if not (0 <= to_index - 1 <= len(self.bot.queues[ctx.guild.id])):
                to_index = len(self.bot.queues[ctx.guild.id]) + 1

            self.bot.queues[ctx.guild.id].insert(to_index - 1, song)
            await ctx.send(f"Spostata {song['title']} dalla posizione {from_index} alla posizione {to_index}")
        else:
            await ctx.send("Oh! mi stai prendendo per il culo o culando per il prendo?")

    @commands.command(name='shuffle')
    async def shuffle(self, ctx):
        if ctx.guild.id in self.bot.queues and self.bot.queues[ctx.guild.id]:
            random.shuffle(self.bot.queues[ctx.guild.id])
            await ctx.send("Coda sminchiata!")
        else:
            await ctx.send("Non c'è un cazzo proprio")

    @commands.command(name='jump')
    async def jump(self, ctx, index: int = None):
        if index == None:
            await ctx.send("Devi specificare la posizione *wink* della canzone a cui vuoi saltare.")
            return

        guild_id = ctx.guild.id

        if guild_id not in self.bot.queues or not self.bot.queues[guild_id]:
            await ctx.send("La coda è vuota.")
            return

        if not (1 <= index <= len(self.bot.queues[guild_id])):
            await ctx.send(f"Posizione non valida. La coda ha {len(self.bot.queues[guild_id])} canzoni.")
            return
        
        if self.bot.looping.get(guild_id) and self.bot.queues[guild_id] and self.bot.queues[guild_id][0].get('is_loop_item'):
            self.bot.queues[guild_id][0]['is_loop_item'] = False

        song_to_jump = self.bot.queues[guild_id].pop(index - 1)
        
        self.bot.queues[guild_id].insert(0, song_to_jump)

        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        else:
            await self.play_next(ctx)
        
        await ctx.send(f"Saltato a: {song_to_jump['title']} 🎶")

    @commands.command(name='muvt')
    async def parti(self, ctx):
        guild_id = ctx.guild.id

        if not ctx.voice_client:
            await ctx.send("Non sono connesso a nessun canale vocale.")
            return

        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            self.bot.paused_state[guild_id] = False
            await ctx.send("Riproduzione ripresa. ▶️")
            return

        if ctx.voice_client.is_playing():
            await ctx.send("Non ti basta quello che faccio gia... ૮(˶ㅠ︿ㅠ)a")
            return 
        if guild_id in self.bot.queues and self.bot.queues[guild_id]:
            await ctx.send("OH E N'ATTIMO CRISTO")
            await self.play_next(ctx)
        else:
            await ctx.send("La coda è vuota cretino")

# SESSO CON EMOJI

    @commands.command(name='🥚')
    async def egg_command(self, ctx):
        now = datetime.datetime.now()
        guild_id = ctx.guild.id

        if not ctx.message.author.voice:
            await ctx.send("Devi essere in un canale vocale per usare questo comando!")
            return

        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()

        url = None
        if now.month == 10:
            await ctx.send("Spooky time 🎃")
            url = "https://youtu.be/sVjk5nrb_lI?si=s78pQFh_1JpiUmv2"
        elif now.month == 11:
            await ctx.send("Resisti bro…")
            url = "https://youtu.be/y0Dix9cIlvA?si=sPHmGGCBAYJxT46g"
        elif now.month == 9 and now.day == 21:
            await ctx.send("So… you remembered")
            url = "https://youtu.be/Gs069dndIYk?si=jpC0TuweymBTN5hu"
        else:
            await ctx.send("Waiting for something to happen?")
            return

        if url:
            try:
                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
                ctx.voice_client.play(player)
            except Exception as e:
                await ctx.send(f"Errore durante la riproduzione: {str(e)}")
        else:
            await ctx.send("Nessun URL valido per l'evento corrente.")
    
    #-------------EMOJI SINGOLE (3)-------------#
    @commands.command(name='🎰', aliases=["🎲", "gambling"]) #ok (di nuovo)
    async def emoji1_1(self, ctx):
            url_lose = "https://www.youtube.com/watch?v=OBYQ4f9100A"
            url_win = "https://youtu.be/QoMhjKbb1Ac?feature=shared"  

            if not ctx.voice_client:
                channel = ctx.message.author.voice.channel
                await channel.connect()

            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
                guild_id = ctx.guild.id
                if guild_id in self.bot.queues:
                    self.bot.queues[guild_id] = []
                if guild_id in self.bot.looping:
                    self.bot.looping[guild_id] = False

            roll = random.randint(1, 1000)

            if roll == 1:
                await ctx.send("nat 1 adios")
                await asyncio.sleep(4)
                await self.bot.close()
            elif roll == 1000:
                try:
                    player = await YTDLSource.from_url(url_win, loop=self.bot.loop, stream=True, executor=self.bot.executor) 
                    stop_winning_event = asyncio.Event()
                    async def winning_loop(ctx, stop_event):
                        await ctx.send("LET'S GO GAMBLING!!")
                        await asyncio.sleep(2)
                        while not stop_event.is_set():
                            await ctx.send("I CAN'T STOP WINNING!!!")
                            await asyncio.sleep(2)

                    winning_task = asyncio.create_task(winning_loop(ctx, stop_winning_event))
                    def after_win_song(error):
                        if error:
                            print(f"Errore durante la riproduzione url_win: {error}")
                        stop_winning_event.set()
                        pass

                    ctx.voice_client.play(player, after=after_win_song)
                except Exception as e:
                    await ctx.send(f"Errore durante la riproduzione dell'URL perdente: {str(e)}")
                    print(f"DEBUG: Exception playing url_lose: {e}")
            else:
                try:
                    player = await YTDLSource.from_url(url_lose, loop=self.bot.loop, stream=True, executor=self.bot.executor) 
                    stop_dangit_event = asyncio.Event()
                    async def aww_dangit_loop(ctx, stop_event):
                        await ctx.send("LET'S GO GAMBLING!!")
                        await asyncio.sleep(1)
                        while not stop_event.is_set():
                            await ctx.send("AWW DANGIT!!!")
                            await asyncio.sleep(1)

                    dangit_task = asyncio.create_task(aww_dangit_loop(ctx, stop_dangit_event))
                    def after_lose_song(error):
                        if error:
                            print(f"Errore durante la riproduzione url_lose: {error}")
                        stop_dangit_event.set()
                        pass

                    ctx.voice_client.play(player, after=after_lose_song)
                except Exception as e:
                    await ctx.send(f"Errore durante la riproduzione dell'URL perdente: {str(e)}")
                    print(f"DEBUG: Exception playing url_lose: {e}")

    @commands.command(name='🇭') #ok
    async def emoji1_2(self, ctx):
        await ctx.send(f"H 👍") #messaggio
        url = "https://www.youtube.com/watch?v=SgMfVnEm4a4" #video
        
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player)
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    @commands.command(name='🐺') #oko
    async def emoji1_3(self, ctx):
        message = await ctx.send(f"AUUUUUUUUUUUUUUUUUUUUUUUUUUU") #messaggio
        url = "https://www.youtube.com/watch?v=7BJ3ZXpserc" #video
        
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            await asyncio.sleep(184)
            await message.edit(content="https://tenor.com/view/funny-emo-wolf-werewolf-transform-gif-27196401")
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    #-------------EMOJI DOPPIE (4)-------------
    
    @commands.command(name='💀🎸', aliases=["🎸💀", "💀🔥", "🔥💀"]) #ok
    async def emoji2_1(self, ctx): # G
        message = await ctx.send(f"G!") #messaggio
        url = "https://www.youtube.com/watch?v=nqgUG_JVzCs" #video
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            await asyncio.sleep(1)
            await message.edit(content ="https://tenor.com/view/bone-gif-9583965047034155743")
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    async def _loading_animation(self, initial_message):
        try:
            message = initial_message
            await asyncio.sleep(4)
            await message.edit(content="Hi") 
            await asyncio.sleep(0.1)
            await message.edit(content="ひ")
            await asyncio.sleep(4)
            await message.edit(content="ひb")
            await asyncio.sleep(4)
            await message.edit(content="ひba") 
            await asyncio.sleep(0.1)
            await message.edit(content="ひば")
            await asyncio.sleep(4)
            await message.edit(content="ひばn")
            await asyncio.sleep(4)
            await message.edit(content="ひばna") 
            await asyncio.sleep(0.1)
            await message.edit(content="ひばな")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"DEBUG: Il traduttore fa schifo: {e}")
    @commands.command(name='💙🌹', aliases=["🌹💙", "hibana", "Hibana","🌹🟦", "🟦🌹"])
    async def emoji2_2(self, ctx):
        playlist_url = "https://music.youtube.com/playlist?list=PLn7FTV8ZetxiXdj7ohp7AqWiYu6X7Z0Cg" # Cambia questo!

        if not ctx.message.author.voice:
            await ctx.send("Devi essere in un canale vocale per usare questo comando!")
            return

        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()

        loading_message = await ctx.send("H")
        animation_task = asyncio.create_task(self._loading_animation(loading_message))

        try:
            ytdl_opts_for_playlist = {**ytdl_format_options}
            ytdl_opts_for_playlist['extract_flat'] = 'webpage_url'
            ytdl_opts_for_playlist['noplaylist'] = False
            temp_ytdl = youtube_dl.YoutubeDL(ytdl_opts_for_playlist)

            raw_info = await self.bot.loop.run_in_executor(self.bot.executor,lambda: temp_ytdl.extract_info(playlist_url, download=False, process=True))

            info_list = []
            if 'entries' in raw_info and raw_info.get('_type') in ['playlist', 'multi_video']:
                info_list = raw_info['entries']
            elif raw_info:
                info_list = [raw_info]
            
            if not info_list:
                raise ValueError("Nessun brano valido trovato o video non disponibile/privato nella playlist.")

            guild_id = ctx.guild.id
            if guild_id not in self.bot.queues:
                self.bot.queues[guild_id] = []

            added_songs = 0
            skipped_songs = 0

            for index, entry in enumerate(info_list):
                if not isinstance(entry, dict):
                    print(f"DEBUG: Skipping non-dictionary entry: {entry}")
                    skipped_songs += 1
                    continue

                video_url = entry.get('webpage_url') or entry.get('url')
                video_title = entry.get('title')

                if video_url and video_title:
                    if entry.get('is_unavailable') or entry.get('private'):
                        skipped_songs += 1
                        print(f"DEBUG: Skipping explicitly unavailable/private entry: {video_title} ({video_url})")
                        continue
                    self.bot.queues[ctx.guild.id].append({'title': video_title, 'url': video_url})
                    added_songs += 1
                else:
                    skipped_songs += 1
                    print(f"DEBUG: Skipping entry with missing URL or title: {entry.get('title', 'N/A')} ({entry.get('webpage_url', 'N/A')})")

            if not (ctx.voice_client.is_playing() or self.bot.paused_state.get(guild_id, False)):
                if self.bot.queues[guild_id]:
                    await self.play_song(ctx, self.bot.queues[guild_id][0]['url'])
                else:
                    await ctx.send("La coda è vuota, impossibile avviare la riproduzione.")

        except Exception as e:
            await ctx.send(f"Errore durante il caricamento: {str(e)}")
            print(f"DEBUG: Exception in emoji2_2 command: {e}")
        finally:
            animation_task.cancel()
            try:
                await animation_task
            except asyncio.CancelledError:
                pass

        await ctx.send(":fire:")
    
    async def _sex_trucks(self, initial_message):
        try:
            message = initial_message
            await asyncio.sleep(19.5)
            await message.edit(content="Two trucks having sex") 
            await asyncio.sleep(2)
            await message.edit(content="Two trucks having sex (di nuovo)")
            await asyncio.sleep(1.5)
            await message.edit(content="My muscles")
            await asyncio.sleep(0.7)
            await message.edit(content="My muscles, my muscles") 
            await asyncio.sleep(1.5)
            await message.edit(content="Involuntarily flex ")
            await asyncio.sleep(2)
            await message.edit(content="Two trucks having sex") 
            await asyncio.sleep(1.5)
            await message.edit(content="Two trucks having sex (di nuovo)")
            await asyncio.sleep(1.5)
            await message.edit(content="My muscles")
            await asyncio.sleep(0.7)
            await message.edit(content="My muscles, my muscles") 
            await asyncio.sleep(1.5)
            await message.edit(content="Involuntarily flex ")
            await asyncio.sleep(1)
            await message.edit(content="TWO PICKUP TRUCKS")
            await asyncio.sleep(3)
            await message.edit(content="MAXING LOVE")
            await asyncio.sleep(1)
            await message.edit(content="AMERICAN MADE")
            await asyncio.sleep(2)
            await message.edit(content="BUILT FORD TOUGH TWO BEAUTIFUL")
            await asyncio.sleep(3.6)
            await message.edit(content="MURDER MACHINES AMERICAN ANGELS ")
            await asyncio.sleep(2)
            await message.edit(content="IN THE SKY")
            await asyncio.sleep(2)
            await message.edit(content="GROWN MEN CRY")
            await asyncio.sleep(2)
            await message.edit(content="(non mi va di scrivere tutto il testo)")
            await asyncio.sleep(3)
            await message.edit(content="https://tenor.com/view/shut-up-two-trucks-is-playing-mario-dance-gif-20465547")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"DEBUG: no sex")
    @commands.command(name='🚚🚚', aliases=["🚚❤️🚚"]) #ok
    async def emoji2_3(self, ctx):
        loading_message = await ctx.send(f"sing with me") #messaggio
        url = "https://youtu.be/WchseC9aKTU?si=Zg_XNFNgQDk0ebMp" #video
        
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            animation_task = await asyncio.create_task(self._sex_trucks(loading_message))
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")
            print(f"DEBUG: Exception in emoji2_3 command: {e}")
            animation_task.cancel()

    @commands.command(name='🐻🍕') #ok
    async def emoji2_4(self, ctx):
        message = await ctx.send(f"AHR AHR AHRAHR AHR") #messaggio

        roll = random.randint(1, 10)
        if roll >= 1 and roll <= 4:
            url = "https://youtu.be/fahtB8vTREc?si=foDuEegFLE0RkXqq"
        elif roll > 4 and roll <= 9:
            url = "https://youtu.be/l18A5BOTlzE?si=rlkRKpnLtd5WlhnD"
        else:
            url = "https://www.youtube.com/shorts/Lpau5V2jLAE"
        
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")
    
    @commands.command(name='🥖🍐', aliases=["🍐🥖"]) #ok
    async def emoji2_5(self, ctx):
        message = await ctx.send("https://tenor.com/view/teto-kasane-kasane-teto-baguette-aymenzero-gif-17694879563690397686")
        url = "https://youtu.be/Soy4jGPHr3g?si=b_9iRS7Av1--mLzy"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            await asyncio.sleep(1)
            await message.edit(content= "https://tenor.com/view/teto-kasane-teto-teto-plush-kasane-teto-plush-crush-it-gif-16166927453889012815")
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    @commands.command(name='voglio', aliases=["😮👌"]) #ok
    async def emoji2_6(self, ctx):
        await ctx.send("Mo metto tutto n'attimo")
        url = "https://www.youtube.com/playlist?list=PLn7FTV8ZetxhkOqYT7DAAXeeA0_KpVEtn"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            ytdl_opts_for_playlist = {**ytdl_format_options}
            ytdl_opts_for_playlist['extract_flat'] = 'webpage_url'
            ytdl_opts_for_playlist['noplaylist'] = False
            temp_ytdl = youtube_dl.YoutubeDL(ytdl_opts_for_playlist)

            raw_info = await self.bot.loop.run_in_executor(self.bot.executor,lambda: temp_ytdl.extract_info(url, download=False, process=True))

            info_list = []
            if 'entries' in raw_info and raw_info.get('_type') in ['playlist', 'multi_video']:
                info_list = raw_info['entries']
            elif raw_info:
                info_list = [raw_info]
            
            if not info_list:
                raise ValueError("Nessun brano valido trovato o video non disponibile/privato nella playlist.")

            guild_id = ctx.guild.id
            if guild_id not in self.bot.queues:
                self.bot.queues[guild_id] = []
            
            added_songs = 0
            skipped_songs = 0

            for index, entry in enumerate(info_list):
                if not isinstance(entry, dict):
                    print(f"DEBUG: Skipping non-dictionary entry: {entry}")
                    skipped_songs += 1
                    continue

                video_url = entry.get('webpage_url') or entry.get('url')
                video_title = entry.get('title')

                if video_url and video_title:
                    if entry.get('is_unavailable') or entry.get('private'):
                        skipped_songs += 1
                        print(f"DEBUG: Skipping explicitly unavailable/private entry: {video_title} ({video_url})")
                        continue
                    self.bot.queues[ctx.guild.id].append({'title': video_title, 'url': video_url})
                    added_songs += 1
                else:
                    skipped_songs += 1
                    print(f"DEBUG: Skipping entry with missing URL or title: {entry.get('title', 'N/A')} ({entry.get('webpage_url', 'N/A')})")

            if ctx.guild.id in self.bot.queues and self.bot.queues[ctx.guild.id]:
                random.shuffle(self.bot.queues[ctx.guild.id])

            if not (ctx.voice_client.is_playing() or self.bot.paused_state.get(guild_id, False)):
                if self.bot.queues[guild_id]:
                    await self.play_song(ctx, self.bot.queues[guild_id][0]['url'])
                else:
                    await ctx.send("La coda è vuota, impossibile avviare la riproduzione.")

        except Exception as e:
            await ctx.send(f"Errore durante il caricamento: {str(e)}")
            print(f"DEBUG: Exception in voglio: {e}")


    #-------------EMOJI TRIPLE (3)-------------
    @commands.command(name='🟦🟥🟨', aliases=["🟦🟨🟥", "🟨🟦🟥", "🟨🟥🟦", "🟥🟨🟦", "🟥🟦🟨", "🟥🟦", "🟦🟥"])
    async def emoji3_1(self, ctx): #indizio: tre scemi (ordine indifferente) (se non ne ricordi uno va bene) (quadrati)
        if ctx.invoked_with == "🟥🟦" or ctx.invoked_with == "🟦🟥":
            await ctx.send(f"Aren't you forgetting someone?")
            await ctx.send(f"https://tenor.com/view/neru-phone-yellow-vocaloid-yellow-vocaloid-gif-6672126422191753106")
            return
        message =await ctx.send(f"YOU REMEMBERED THE YELLOW ONE") #messaggio
        url = "https://www.youtube.com/watch?v=duPJqfKiA78" #video
        
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            await asyncio.sleep(1)
            await message.edit(content = "https://tenor.com/view/hatsune-miku-triple-baka-braincells-gif-17994396760098916322")
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    @commands.command(name='🫵6️🤪', aliases=["🫵6️⃣😜", "🫵6️⃣🫨"]) #ok
    async def emoji3_2(self, ctx):
        message = await ctx.send("TU SEI PAZZO")
        roll = random.randint(1,10)
        if roll == 7:
            url = "https://music.youtube.com/watch?v=neVn4FvfYBU&si=j1UN7DYJnbTHbu17"
        else: url = "https://music.youtube.com/watch?v=2hB_0dQZz3Y&si=fHoXqiKmhKM_fs7y"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            await asyncio.sleep(5)
            await message.edit(content= "https://tenor.com/view/caparezza-coniglio-gif-24882977")
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    @commands.command(name='💃💃💃', aliases=["💃🇸🇪🍬", "💃🍬🇸🇪", "🇸🇪🍬💃", "🇸🇪💃🍬", "🍬🇸🇪💃","🍬💃🇸🇪"]) #ok
    async def emoji3_3(self, ctx):
        message = await ctx.send("https://tenor.com/view/caramelldansen-dance-gif-12297359456353562512")
        url = "https://youtu.be/KvP1y9P453g?si=NSH3L2uv3J_9_DLM"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            await asyncio.sleep(20)
            await message.edit(content= "https://tenor.com/view/cat-gif-26538514")
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")
    
    
    #-------------TOBY FOX (10)-------------
    @commands.command(name='💀', aliases=["💀🟦", "💀🟥", "🟥💀", "🟦💀", "💀🧣", "🧣💀"]) #ok
    async def emoji1_TF(self, ctx):
        if ctx.invoked_with == "💀":
            await ctx.send("Eh si ma quale dei due?")
            return
        elif ctx.invoked_with == "💀🟥" or ctx.invoked_with == "🟥💀" or ctx.invoked_with == "💀🧣" or ctx.invoked_with == "🧣💀":
            url = "https://youtu.be/AKAiUtWZ4xY?si=zbI7yM_Y_ewpVETj"
        elif ctx.invoked_with == "🟦💀" or ctx.invoked_with == "💀🟦":
            url = "https://youtu.be/KK3KXAECte4?si=RajOpr8e2b75ML3w"
        
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    @commands.command(name='🎃🫳🩰❤', aliases=["🎃", "🎃❤🩰"]) #ok
    async def emoji2_TF(self, ctx):
        if ctx.invoked_with == "🎃":
            await ctx.send("Y O U  A R E  T A K I N G  T O O  L O N G")
        elif ctx.invoked_with == "🎃🫳🩰❤":
            await ctx.send("Y O U  A R E   T O O  T O O")
        elif ctx.invoked_with == "🎃❤🩰":
            await ctx.send("Y O U  A R E  T A K I N G   T O O  T O O")
        url = "https://youtu.be/K-ifukvnICY?si=-06MfZ2rTwT_fFZq"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")
    
    async def _tenna_load(self, initial_message):
        try:
            message = initial_message
            await asyncio.sleep(1)
            await message.edit(content= "T")
            await asyncio.sleep(1)
            await message.edit(content= "V")
            await asyncio.sleep(1)
            await message.edit(content= "TIIIIME")
            await asyncio.sleep(2)
            await message.edit(content= "https://tenor.com/view/deltarune-chapter-ch-3-ant-gif-4924904170325380742")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"DEBUG: Il traduttore fa schifo: {e}")
    @commands.command(name="📺⏲", alises=["📺📡", "📡"]) #ok
    async def emoji3_TF(self, ctx):
        message = await ctx.send("IT'S")
        animation_task = await asyncio.create_task(self._tenna_load(message))
        url = "https://www.youtube.com/watch?v=F2PJbTuZlTU"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            await asyncio.sleep(2)
            await message.edit(content="https://media.discordapp.net/attachments/767050357527412817/1382276386386874378/deltarune-tenna.gif?ex=687b5833&is=687a06b3&hm=28b81b8841c9bc6e20311a081b7abf95ecebe2346e1c5b20cacdd88624b8b80d&=&width=151&height=250")
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")
            animation_task.cancel()

    @commands.command(name='🟪🟨', aliases=["📬","🟣🟡","🔴🟡", "🕴", "[[Emoji]]", "[[Emojis]]", "[[HyperlinkBlocked]]", "[[Hyperlink_Blocked]]"]) #ok
    async def emoji4_TF(self, ctx):
        message = await ctx.send("TEMPO DI SENTIRE [[Hyperlink_Blocked]]!!!")
        url = "https://youtu.be/V31PVkwzpEY?si=t4x2w8E1pn6AW_aD"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            await asyncio.sleep(1)
            await message.edit(content= "https://tenor.com/view/spamton-deltarune-yippee-creature-marmarmiya-gif-1523836643939819852")
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")
    
    @commands.command(name='🎠🃏', aliases=["🃏🎠"]) #ok
    async def emoji5_TF(self, ctx):
        message = await ctx.send("I AM INNOCENT, INNOCENT. I JUST WANTED TO PLAY A GAME, GAME.")
        url = "https://music.youtube.com/watch?v=Z01Tsgwe2dQ&si=Fvb_uf2KDiAr3BKa"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            await asyncio.sleep(1)
            await message.edit(content= "https://tenor.com/view/jevil-deltarune-spin-spinning-revolving-gif-8580457429097453899")
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    @commands.command(name='🎤😺🎙', aliases=["🎤🎙😺", "😺🎤🎙", "😺🎙🎤", "🎙😺🎤", "🎙🎤😺", "📺🗣🎙", "📺🗣🎤", "📺🗣😺"]) #ok
    async def emoji6_TF(self, ctx):
        if ctx.invoked_with == "📺🗣🎙" or ctx.invoked_with == "📺🗣🎤" or ctx.invoked_with == "📺🗣😺":
            await ctx.send("https://tenor.com/view/deltarune-undertale-tenna-mr-tenna-delta-rune-gif-17589151662349103396")
            url="https://music.youtube.com/watch?v=_iQ6fgFcPwM&si=IWaE-VA_e05Tnb5U"
        else:
            await ctx.send("WHO THE FUCK IS MIKE???")
            url="https://music.youtube.com/watch?v=r-DvoCTarMQ&si=3E4lR90YODisI-38"
        
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    @commands.command(name='🐐🍰', aliases=["🍰🐐", "🐐👑🍰", "🍰👑🐐", "🐐🍰👑", "🍰🐐👑", "🐐💀", "💀🐐"]) #ok
    async def emoji7_TF(self, ctx):
        await ctx.send("https://tenor.com/view/deltarune-deltarune-chapter-4-undertale-dance-sans-gif-16319988285385147744")
        if ctx.invoked_with == "💀🐐" or ctx.invoked_with == "🐐💀":
            url = "https://youtu.be/okigoGIe9RQ?si=AcVTdr2qkw3qSbT4"
        else: 
            url = "https://music.youtube.com/watch?v=XJ9XtKJHvjQ&si=M9BQXp7jlKGAfxoD"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")
    
    @commands.command(name='🐶🎵', aliases=["🐶🎶", "🎶🐶", "🎵🐶"]) #ok
    async def emoji8_TF(self, ctx):
        message = await ctx.send("https://tenor.com/view/winking-annoying-dog-toby-gif-26091662")
        url = "https://music.youtube.com/watch?v=c7vfHJOq0H4&si=KhVbJNiQ63ojrDd_"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            await asyncio.sleep(1)
            await message.edit(content= "https://tenor.com/view/spinning-spin-rotate-rotating-pixel-gif-26324892")
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    @commands.command(name='🕷🍵', aliases=["🕷🫖", "🍵🕷", "🫖🕷"]) #better do a syncronised dance with the other spiders
    async def emoji9_TF(self, ctx):
        await ctx.send("https://tenor.com/view/muffet-undertale-undertale-muffet-gif-14614489080104465571")
        url = "https://music.youtube.com/watch?v=NH-GAwLAO30&si=5lI1UuFM7HVhE0wl"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    @commands.command(name='🐢🔨', aliases=["🔨🐢"]) #ok
    async def emoji10_TF(self, ctx):
        message = await ctx.send("https://static.wikia.nocookie.net/deltarune/images/2/20/Text_that_shows_up_when_gerson_recruits_somone.png/revision/latest/scale-to-width-down/185?cb=20250618070509")
        url = "https://music.youtube.com/watch?v=tBdLO8u-0L8&si=-EEkR9HHBK8gTUaR"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            await asyncio.sleep(1)
            await message.edit(content= "https://tenor.com/view/gerson-deltarune-old-man-emote-gif-3077167955114841259")
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    #-------------Graxy (7)-------------
    @commands.command(name='🆎') #ok
    async def emoji1_Gx(self, ctx):
        message = await ctx.send("Aspetta fammi fare")
        url = "https://youtu.be/gVYsd3H3YJc?si=KnfvjYBwWn-5EHca"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            await asyncio.sleep(16)
            await message.edit(content= "Rap futuristico A-B\nRap futuristico AB-AB-AB-AB\nRap futuristico Fa-bri\nRap futuristico Fabri-Fabri-Fabri-Fabri\nRap turubistico B-A\nSpeperteristico Fibra-Fibra-Fibra-Fibra\nSpeperefistico C-D\nRap futuristico")
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    @commands.command(name='🅰️🅾️') #ok
    async def emoji2_Gx(self, ctx):
        await ctx.send("https://klipy.com/gifs/francesco-totti-roma-era")
        url = "https://youtu.be/39G3w4PoiBk?si=RZQo18aa2b5DvHmv"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    @commands.command(name='😠🔫') #ok
    async def emoji3_Gx(self, ctx):
        message = await ctx.send("https://klipy.com/gifs/persona-persona3-25")
        url = "https://www.youtube.com/watch?v=e2Gyaqf7EoU"
        capa = "https://youtu.be/1nfgKWbC3WU?si=JpRDflpFO7zPL8Uq"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()

        roll = random.randint(1, 5)#wheel of fortune
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
                
            if roll<=2:
                player = await YTDLSource.from_url(capa, loop=self.bot.loop, stream=True, executor=self.bot.executor)
                ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
                await asyncio.sleep(23)
                await message.edit(content= "https://c.tenor.com/jjniJAxlSF4AAAAd/tenor.gif")
            else:
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
                ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    @commands.command(name='🍌👨', aliases=["👨🍌"]) #ok
    async def emoji4_Gx(self, ctx):
        message = await ctx.send("Ladies and gentlemen")
        url = "https://music.youtube.com/watch?v=BRD9BqjIk-E&si=By19vQzqFVK8KVf7"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            await asyncio.sleep(1)
            await message.edit(content= "Colonel PT Chester Whitmore is proud to present Bung Vulchungo and the Zimbabwe Songbirds")
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    @commands.command(name='🇷🇺🎻', aliases=["🎻🇷🇺"]) #ok
    async def emoji5_Gx(self, ctx):
        await ctx.send("https://klipy.com/gifs/just-dance-just-dance-unlimited")
        url = "https://music.youtube.com/watch?v=5Z0dxsFmX7c"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")
    
    @commands.command(name='🐸💥⚰️', aliases=["🐸⚰️💥","⚰️💥🐸","⚰️🐸💥","💥🐸⚰️","💥⚰️🐸"]) #ok
    async def emoji6_Gx(self, ctx):
        message = await ctx.send("https://klipy.com/gifs/frog-king-shrek")
        url = "https://music.youtube.com/watch?v=1PLAU_PXboc&si=vY2h5xs1h_lK3Fgd"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            await asyncio.sleep(35)
            await message.edit(content= "https://klipy.com/gifs/shrek-frogs")
        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    @commands.command(name='🐴🕴️🐴') #ok
    async def emoji7_Gx(self, ctx):
        await ctx.send("https://c.tenor.com/EVdoy3vGSWUAAAAC/tenor.gif")
        url = "https://music.youtube.com/watch?v=4AgDYTuZWOw"
        if not ctx.voice_client:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        try:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, executor=self.bot.executor)
            ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
            await asyncio.sleep(5)
            await ctx.send("https://c.tenor.com/IVAEcBO8RYoAAAAd/tenor.gif")
            await asyncio.sleep(10)
            await ctx.send("https://c.tenor.com/2dBRFtODSjUAAAAC/tenor.gif")
            await asyncio.sleep(10)
            await ctx.send("https://tenor.com/view/dance-winnie-the-pooh-gangnam-style-gif-15240602")
            await asyncio.sleep(20)
            await ctx.send("https://tenor.com/view/fnaf-2-puppet-gangnam-style-gif-5017865932531913760")
            await asyncio.sleep(20)
            await ctx.send("https://tenor.com/view/cat-dancing-cat-cat-doing-gangnam-style-gangnam-style-gangnam-gif-15237305187829730215")
            await asyncio.sleep(1)
            await ctx.send("https://tenor.com/view/goku-fortnite-gangnam-style-gif-26491338")
            await asyncio.sleep(1)
            await ctx.send("https://tenor.com/view/neco-neco-arc-neco-arc-dance-neco-arc-dancing-gangnam-style-gif-26776142")
            await asyncio.sleep(1)
            await ctx.send("https://tenor.com/view/sonic-dance-gangnam-style-gif-10228495687541789966")
            await asyncio.sleep(1)
            await ctx.send("https://tenor.com/view/oppa-gangnam-style-hatsune-miku-kagamine-rin-defoko-uta-utatane-gif-26387824")
            await asyncio.sleep(20)
            await ctx.send("https://tenor.com/view/uzbekistan-gif-6547847269052440336")
            await asyncio.sleep(20)
            await ctx.send("https://tenor.com/view/vtuber-hakos-baelz-gangnam-style-hakos-baelz-gangnam-hakos-baelz-cope-gif-27629132")
            await asyncio.sleep(20)
            await ctx.send("https://tenor.com/view/gangnam-style-dance-gif-12987815365782390545")
            await asyncio.sleep(10)
            await ctx.send("https://c.tenor.com/BcbDECFlC14AAAAC/tenor.gif")
            await asyncio.sleep(15)
            await ctx.send("https://c.tenor.com/lxgFoaNwCMAAAAAd/tenor.gif")
            await asyncio.sleep(20)
            await ctx.send("https://c.tenor.com/-e1FKk-2gloAAAAC/tenor.gif")
            await asyncio.sleep(15)
            await ctx.send("https://c.tenor.com/ZaEFxAQRtpwAAAAd/tenor.gif")

        except Exception as e:
            await ctx.send(f"Errore durante la riproduzione: {str(e)}")

    class GithubDocsMenu(View):
        def __init__(self, ctx, file_contents):
            super().__init__(timeout=300)
            self.ctx = ctx
            self.file_contents = file_contents
            self.current_page = 0

        async def update_embed(self, interaction):
            embed = self.get_embed()
            await interaction.response.edit_message(embed=embed, view=self)

        def get_embed(self):
            if not self.file_contents:
                return discord.Embed(title="Nessun documento disponibile", description="Impossibile caricare i documenti da GitHub.", color=discord.Color.red())

            url, content = self.file_contents[self.current_page]
            
            if self.current_page + 1 == 1:
                titolo="Istruzioni"
            elif self.current_page + 1 == 2:
                titolo="Single Emoji hints"
            elif self.current_page + 1 == 3:
                titolo="Double Emoji hints"
            elif self.current_page + 1 == 4:
                titolo="Triple Emoji hints"
            elif self.current_page + 1 == 5:
                titolo="Toby Fox hints"
            elif self.current_page + 1 == 6:
                titolo="Graxy fa game dev se i puzzle fanno schifo blastate lei"
            else:
                titolo="Hints" 

            embed = discord.Embed(
                title=titolo,
                description=content,
                color=0xFF00FF
            )
            embed.set_footer(text=f"Pagina {self.current_page + 1}/{len(self.file_contents)}")
            return embed

        @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary, custom_id="prev_page")
        async def previous_page(self, interaction: discord.Interaction, button: Button):
            self.current_page = (self.current_page - 1 + len(self.file_contents)) % len(self.file_contents)
            await self.update_embed(interaction)

        @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary, custom_id="next_page")
        async def next_page(self, interaction: discord.Interaction, button: Button):
            self.current_page = (self.current_page + 1) % len(self.file_contents)
            await self.update_embed(interaction)

    @commands.command(name='hints', aliases=['hint'])
    async def github_docs(self, ctx):
        github_file_urls = [
            "https://gist.githubusercontent.com/Panzu4/6b0c3c227ac0fd3ada0d9fdf1e62ae8e/raw/instr.txt",
            "https://gist.githubusercontent.com/Panzu4/2da4848bf95ac05a2a26eb82bd83452a/raw/Emoji_1.txt",
            "https://gist.githubusercontent.com/Panzu4/1ac7e6ae7ec8302e1b866e304a4a03bc/raw/Emoji_2.txt",
            "https://gist.githubusercontent.com/Panzu4/272303c11ef6cc71ee6cb72924dcd7d6/raw/Emoji_3.txt",
            "https://gist.githubusercontent.com/Panzu4/2296ab8823dae80cb4f6b0e076002de8/raw/toby.txt",
            "https://gist.githubusercontent.com/Panzu4/27c4b69a8a62e8a53f080c5487fa9a98/raw/graz.txt",
        ]

        roll = random.randint(1, 20)
        if roll == 7 or roll == 14:
            loading_message = await ctx.send("https://c.tenor.com/4UnrcVLKeHUAAAAd/tenor.gif")
            await asyncio.sleep(5)
        elif roll == 4:
            loading_message = await ctx.send("Mike, roll the music")
            if not ctx.voice_client:
                channel = ctx.message.author.voice.channel
                await channel.connect()
            if not ctx.voice_client.is_playing():
                url_video = "https://youtu.be/YsZoTTl59hg?si=xWO4D1moMN7sGw7G"
                player = await YTDLSource.from_url(url_video, loop=self.bot.loop, stream=True, executor=self.bot.executor)
                ctx.voice_client.play(player, after=lambda e: self.bot.loop.call_soon_threadsafe(asyncio.create_task, self.play_next(ctx)))
        else:
            loading_message = await ctx.send("Mike, the hints")

        fetched_contents = []
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in github_file_urls:
                tasks.append(self._fetch_github_file_content(session, url))
            
            results = await asyncio.gather(*tasks)

            for url, content in zip(github_file_urls, results):
                if content:
                    if len(content) > 4000:
                        content = content[:4000] + "\n... (contenuto troncato)"
                    fetched_contents.append((url, content))
                else:
                    print(f"DEBUG: Fallito il recupero del contenuto per: {url}")

        if not fetched_contents:
            await loading_message.edit(content="Errore: Impossibile caricare alcun documento dai link forniti. Assicurati che gli URL siano corretti e i file esistano.")
            return


        view = self.GithubDocsMenu(ctx, fetched_contents)
        initial_embed = view.get_embed()
        await loading_message.edit(content=None, embed=initial_embed, view=view)

    async def _fetch_github_file_content(self, session, url):
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        try:
            timestamp_url = f"{url}?_t={int(datetime.datetime.now().timestamp())}"
            async with session.get(timestamp_url, headers=headers) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Errore HTTP {response.status} per {url}")
                    return None
        except aiohttp.ClientError as e:
            print(f"Errore di rete per {url}: {e}")
            return None
        except Exception as e:
            print(f"Errore generico durante il recupero di {url}: {e}")
            return None

    @commands.group(name='H', aliases=["h"])
    async def h_h(self, ctx):
        await ctx.send("H 👍")

class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="aiutp")
    async def help_command(self, ctx, page: int = 1):
        view = HelpMenu(ctx)
        view.current_page = page
        embed = view.get_embed()
        await ctx.send(embed=embed, view=view)

# BOT SETUP
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
bot.queues = {}
bot.looping = {}
bot.paused_state = {}

async def save_state():
    serializable_queues = {str(guild_id): queue for guild_id, queue in bot.queues.items()}
    serializable_looping = {str(guild_id): loop_status for guild_id, loop_status in bot.looping.items()}
    serializable_paused_state = {str(guild_id): paused_status for guild_id, paused_status in bot.paused_state.items()}
    
    state = {
        'queues': serializable_queues,
        'looping': serializable_looping,
        'paused_state': serializable_paused_state 
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)
    print("Stato del bot salvato.")

async def load_state():
    """Carica lo stato del bot da un file all'avvio."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        bot.queues = {int(guild_id): queue for guild_id, queue in state.get('queues', {}).items()}
        bot.looping = {int(guild_id): loop_status for guild_id, loop_status in state.get('looping', {}).items()}
        bot.paused_state = {int(guild_id): paused_status for guild_id, paused_status in state.get('paused_state', {}).items()} # Add this

        try:
            print(f"File caricato con successo.")
        except OSError as e:
            print(f"Errore durante il caricamento del file '{STATE_FILE}': {e}")

@bot.event
async def on_ready():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"Bot connesso come {bot.user.name}")
    print(f"Versione: {BOT_VERSION}")
    await load_state()
    bot.loop.create_task(check_connection_quality(bot))

    bot.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    try:
        await bot.add_cog(Music(bot))
        await bot.add_cog(Events(bot))
        await bot.add_cog(HelpCommands(bot))
    except Exception as e:
        print(f"Porco dio un errore sulle funzioni: {e}")

    bot.remove_command("help")

    for guild_id, queue in bot.queues.items():
        if queue:
            guild = bot.get_guild(guild_id)
            if guild and guild.voice_client and not guild.voice_client.is_playing():
                text_channel = None
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        text_channel = channel
                        break
                if text_channel:
                    ctx = await bot.get_context(discord.Message(content="!play_resumed", channel=text_channel, guild=guild, author=bot.user))
                    ctx.voice_client = guild.voice_client
                    music_cog = bot.get_cog('Music')
                    if music_cog:
                        await music_cog.play_next(ctx)

async def check_connection_quality(bot_instance):
    while True:
        latency = bot_instance.latency
        if latency > 0.2:
            print(f"⚠️ AVVISO: Latenza alta - {latency * 1000:.2f} ms")
        await asyncio.sleep(30)

async def check_for_updates_and_interact():
    print("\nVerifica aggiornamenti in corso...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(LATEST_VERSION_URL) as response:
                if response.status == 200:
                    latest_version_str = (await response.text()).strip()

                    current_version = parse_version(BOT_VERSION)
                    latest_version = parse_version(latest_version_str)

                    if current_version < latest_version:
                        print(f"\n==============================================")
                        print(f"  ATTENZIONE: È disponibile una nuova versione!")
                        print(f"  Versione corrente: {BOT_VERSION}")
                        print(f"  Ultima versione:   {latest_version_str}")
                        print(f"==============================================\n")

                        while True:
                            choice = input("Vuoi aggiornare il bot? (S/N): ").strip().lower()
                            if choice == 's':
                                print(f"\n==============================================")
                                print(f"  Apertura del link di aggiornamento nel browser:")
                                print(f"  {RELEASE_URL}")
                                print(f"==============================================\n")
                                webbrowser.open_new_tab(RELEASE_URL)
                                print("Chiusura del bot. Riavvia con la nuova versione dopo il download.")
                                return False
                            elif choice == 'n':
                                print("Continuo con la versione attuale. Potresti perdere nuove funzionalità o correzioni di bug.")
                                return True
                            else:
                                print("Scelta non valida. Per favor, digita 'S' per Sì o 'N' per No.")
                    else:
                        print("Il bot è già aggiornato all'ultima versione.")
                        return True
                else:
                    print(f"Errore durante la verifica degli aggiornamenti (HTTP Status: {response.status}). Impossibile verificare la versione remota.")
                    print("Il bot continuerà l'avvio. Controlla la tua connessione o l'URL di rilascio.")
                    return True
    except Exception as e:
        print(f"Impossibile verificare gli aggiornamenti: {e}. Il bot continuerà l'avvio.")
        print("Controlla la tua connessione internet o l'URL del repository.")
        return True

@bot.command(name='restart')
async def restart_bot(ctx):
    await ctx.send("Riavvia il bot")
    await save_state()
    await bot.close()

@bot.command(name='close', aliases=["chiudi"])
async def close_bot(ctx):
    await ctx.send("https://media.tenor.com/T_Zymb6FIdYAAAAi/deleted.gif")
    await bot.close()

async def main_bot_run():
    """Funzione principale per eseguire il bot, inclusi i controlli degli aggiornamenti."""
    should_run = await check_for_updates_and_interact()
    if should_run:
        try:
            await bot.start(TOKEN)
        except KeyboardInterrupt:
            print("Bot interrotto dall'utente.")
        finally:
            await bot.close()
            if hasattr(bot, 'executor'): 
                bot.executor.shutdown()
    else:
        print("Avvio del bot annullato dall'utente per aggiornamento.")
        sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(main_bot_run())
    except Exception as e:
        print(f"Errore critico durante l'avvio: {e}")