from .base import BaseHandler
import requests
import urllib3
from datetime import datetime

urllib3.disable_warnings()

class DiscordHandler(BaseHandler):
    """
    Handler pour envoyer des messages Discord via un bot.
    Supporte les messages simples et les embeds avec templates Jinja.
    """
    
    def __init__(self, level, formatter, filters=None, ops='>=', async_mode=False, 
                 bot_token=None, guild_id=None, guild_name=None, channel_id=None, 
                 channel_name=None, user_id=None, user_name=None, ssl_verify=True,
                 content=None, embeds=None):
        """
        Args:
            bot_token: Token du bot Discord (requis)
            guild_id: ID du serveur Discord
            guild_name: Nom du serveur Discord (alternative à guild_id)
            channel_id: ID du channel Discord
            channel_name: Nom du channel Discord (alternative à channel_id)
            user_id: ID de l'utilisateur pour un message privé
            user_name: Nom d'utilisateur Discord pour un message privé (alternative à user_id)
            content: Template du message simple (supporte Jinja2)
            embeds: Liste d'embeds avec templates Jinja2 (supporte {{ }} et couleurs hex)
            
        Note: Pour channel_name ou user_name, vous devez fournir guild_id OU guild_name
        """
        super().__init__(level=level, formatter=formatter, filters=filters, ops=ops, async_mode=async_mode)
        
        if not bot_token:
            raise ValueError("DiscordHandler requires 'bot_token' parameter.")
        
        if not channel_id and not channel_name and not user_id and not user_name:
            raise ValueError(
                "DiscordHandler requires either 'channel_id', 'channel_name', "
                "'user_id' or 'user_name'"
            )
        
        if (channel_name or user_name) and not guild_id and not guild_name:
            raise ValueError(
                "DiscordHandler requires 'guild_id' or 'guild_name' when using 'channel_name' or 'user_name'"
            )
        
        self.bot_token = bot_token
        self.guild_id = guild_id
        self.guild_name = guild_name
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.user_id = user_id
        self.user_name = user_name
        self.ssl_verify = ssl_verify
        self.content_template = content
        self.embeds_config = embeds or []
        self.discord_api_base = "https://discord.com/api/v10"
        self._resolved_guild_id = None
        self._resolved_channel_id = None
        self._resolved_user_id = None

    def _get_guild_id_from_name(self):
        """Récupère le guild_id à partir du guild_name."""
        if self._resolved_guild_id:
            return self._resolved_guild_id
        
        url = f"{self.discord_api_base}/users/@me/guilds"
        
        headers = {
            "Authorization": f"Bot {self.bot_token}",
        }
        
        response = requests.get(
            url,
            headers=headers,
            verify=self.ssl_verify
        )
        response.raise_for_status()
        
        guilds = response.json()
        
        for guild in guilds:
            if guild.get("name") == self.guild_name:
                self._resolved_guild_id = guild["id"]
                return guild["id"]
        
        raise ValueError(f"Guild '{self.guild_name}' not found. Available guilds: {[g['name'] for g in guilds]}")

    def _get_channel_id_from_name(self, guild_id):
        """Récupère le channel_id à partir du channel_name."""
        if self._resolved_channel_id:
            return self._resolved_channel_id
        
        url = f"{self.discord_api_base}/guilds/{guild_id}/channels"
        
        headers = {
            "Authorization": f"Bot {self.bot_token}",
        }
        
        response = requests.get(
            url,
            headers=headers,
            verify=self.ssl_verify
        )
        response.raise_for_status()
        
        channels = response.json()
        
        for channel in channels:
            if channel.get("name") == self.channel_name:
                self._resolved_channel_id = channel["id"]
                return channel["id"]
        
        raise ValueError(f"Channel '{self.channel_name}' not found in guild {guild_id}. Available channels: {[c['name'] for c in channels]}")

    def _get_user_id_from_name(self, guild_id):
        """Récupère l'user_id à partir du user_name."""
        if self._resolved_user_id:
            return self._resolved_user_id
        
        url = f"{self.discord_api_base}/guilds/{guild_id}/members/search"
        
        headers = {
            "Authorization": f"Bot {self.bot_token}",
        }
        
        params = {
            "query": self.user_name,
            "limit": 1
        }
        
        response = requests.get(
            url,
            headers=headers,
            params=params,
            verify=self.ssl_verify
        )
        response.raise_for_status()
        
        members = response.json()
        
        if members:
            self._resolved_user_id = members[0]["user"]["id"]
            return members[0]["user"]["id"]
        
        raise ValueError(f"User '{self.user_name}' not found in guild {guild_id}")

    def _hex_to_decimal(self, hex_color):
        """Convertit une couleur hex en décimal."""
        if isinstance(hex_color, int):
            return hex_color
        
        # Supporte #RRGGBB et RRGGBB
        hex_color = str(hex_color).lstrip('#')
        return int(hex_color, 16)

    def _render_template(self, template_str, record):
        """Rend un template Jinja2 avec les données du record."""
        if not template_str:
            return None
        
        template = self.jinja_env.from_string(str(template_str))
        return template.render(record)

    def _build_embeds(self, record):
        """Construit les embeds à partir de la configuration."""
        if not self.embeds_config:
            return None
        
        embeds = []
        for embed_config in self.embeds_config:
            embed = {}
            
            # Traiter chaque champ avec les templates
            if "title" in embed_config:
                embed["title"] = self._render_template(embed_config["title"], record)
            
            if "description" in embed_config:
                embed["description"] = self._render_template(embed_config["description"], record)
            
            # Convertir la couleur hex en décimal
            if "color" in embed_config:
                embed["color"] = self._hex_to_decimal(embed_config["color"])
            
            # Traiter les champs
            if "fields" in embed_config:
                embed["fields"] = []
                for field in embed_config["fields"]:
                    processed_field = {
                        "name": self._render_template(field.get("name"), record),
                        "value": self._render_template(field.get("value"), record),
                        "inline": field.get("inline", False)
                    }
                    embed["fields"].append(processed_field)
            
            # Traiter footer
            if "footer" in embed_config:
                embed["footer"] = {}
                if "text" in embed_config["footer"]:
                    embed["footer"]["text"] = self._render_template(embed_config["footer"]["text"], record)
                if "icon_url" in embed_config["footer"]:
                    embed["footer"]["icon_url"] = self._render_template(embed_config["footer"]["icon_url"], record)
            
            # Traiter author
            if "author" in embed_config:
                embed["author"] = {}
                if "name" in embed_config["author"]:
                    embed["author"]["name"] = self._render_template(embed_config["author"]["name"], record)
                if "url" in embed_config["author"]:
                    embed["author"]["url"] = self._render_template(embed_config["author"]["url"], record)
                if "icon_url" in embed_config["author"]:
                    embed["author"]["icon_url"] = self._render_template(embed_config["author"]["icon_url"], record)
            
            # Traiter image
            if "image" in embed_config:
                if "url" in embed_config["image"]:
                    embed["image"] = {
                        "url": self._render_template(embed_config["image"]["url"], record)
                    }
            
            # Traiter thumbnail
            if "thumbnail" in embed_config:
                if "url" in embed_config["thumbnail"]:
                    embed["thumbnail"] = {
                        "url": self._render_template(embed_config["thumbnail"]["url"], record)
                    }
            
            # Ajouter timestamp si demandé
            if embed_config.get("timestamp", False):
                embed["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
            embeds.append(embed)
        
        return embeds if embeds else None

    def _emit_sync(self, record):
        """Envoie le message à Discord."""
        modified_record = self.formatter.apply_rules(record)
        
        if not self.should_handle(modified_record):
            return
        
        try:
            if self.user_id or self.user_name:
                if self.user_name:
                    guild_id = self.guild_id or self._get_guild_id_from_name()
                    user_id = self.user_id or self._get_user_id_from_name(guild_id)
                else:
                    user_id = self.user_id
                
                self._send_dm(user_id, modified_record)
            else:
                guild_id = self.guild_id or self._get_guild_id_from_name()
                channel_id = self.channel_id or self._get_channel_id_from_name(guild_id)
                self._send_to_channel(channel_id, modified_record)
        except requests.exceptions.RequestException as e:
            print(f"[DiscordHandler] Failed to send message to Discord: {e}")
        except Exception as e:
            print(f"[DiscordHandler] Error: {e}")

    def _send_to_channel(self, channel_id, record):
        """Envoie un message dans un channel."""
        url = f"{self.discord_api_base}/channels/{channel_id}/messages"
        
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }
        
        payload = {}
        
        # Ajouter le contenu simple
        if self.content_template:
            content = self._render_template(self.content_template, record)
            if content:
                payload["content"] = content[:2000]  # Limite Discord
        
        # Ajouter les embeds
        embeds = self._build_embeds(record)
        if embeds:
            payload["embeds"] = embeds
        
        # Si pas de contenu ni d'embeds, utiliser le formatage par défaut
        if not payload:
            content = self.formatter.format(record)
            if len(content) > 1990:
                content = content[:1990] + "..."
            payload["content"] = content
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=self.ssl_verify
        )
        response.raise_for_status()

    def _send_dm(self, user_id, record):
        """Envoie un message privé à un utilisateur."""
        url = f"{self.discord_api_base}/users/@me/channels"
        
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }
        
        payload = {"recipient_id": user_id}
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=self.ssl_verify
        )
        response.raise_for_status()
        
        dm_channel_id = response.json()["id"]
        self._send_message(dm_channel_id, record)

    def _send_message(self, channel_id, record):
        """Envoie un message à un channel spécifique."""
        url = f"{self.discord_api_base}/channels/{channel_id}/messages"
        
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }
        
        payload = {}
        
        # Ajouter le contenu simple
        if self.content_template:
            content = self._render_template(self.content_template, record)
            if content:
                payload["content"] = content[:2000]
        
        # Ajouter les embeds
        embeds = self._build_embeds(record)
        if embeds:
            payload["embeds"] = embeds
        
        # Si pas de contenu ni d'embeds, utiliser le formatage par défaut
        if not payload:
            content = self.formatter.format(record)
            if len(content) > 1990:
                content = content[:1990] + "..."
            payload["content"] = content
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=self.ssl_verify
        )
        response.raise_for_status()