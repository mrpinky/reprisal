from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

from .utils import checks

import re
import random

phrases = ["Eat My Hat"]


class Game:
    def __init__(self, word):
        self.word = word
        # This converts everything but spaces to a blank
        self.blanks = "".join(letter if not re.search("[a-zA-Z0-9]", letter) else "_" for letter in word)
        self.failed_letters = []
        self.guessed_letters = []
        self.fails = 0

    def guess_letter(self, letter):
        # No matter what, add this to guessed letters so we only have to do one check if a letter was already guessed
        self.guessed_letters.append(letter)
        if letter.lower() in self.word.lower():
            # Replace every occurence of the guessed letter, with the correct letter
            # Use the one in the word instead of letter, due to capitalization
            self.blanks = "".join(
                word_letter if letter.lower() == word_letter.lower() else self.blanks[i] for i, word_letter in
                enumerate(self.word))
            return True
        else:
            self.fails += 1
            self.failed_letters.append(letter)
            return False

    def guess_word(self, word):
        if word.lower() == self.word.lower():
            self.blanks = self.word
            return True
        else:
            self.fails += 1
            return False

    def win(self):
        return self.word == self.blanks

    def failed(self):
        return self.fails == 7

    def __str__(self):
        # Here's our fancy formatting for the hangman picture
        # Each position in the hangman picture is either a space, or part of the man, based on how many fails there are
        man = "     ——\n"
        man += "    |  |\n"
        man += "    {}  |\n".format("o" if self.fails > 0 else " ")
        man += "   {}{}{} |\n".format("/" if self.fails > 1 else " ", "|" if self.fails > 2 else " ",
                                      "\\" if self.fails > 3 else " ")
        man += "    {}  |\n".format("|" if self.fails > 4 else " ")
        man += "   {} {} |\n".format("/" if self.fails > 5 else " ", "\\" if self.fails > 6 else " ")
        man += "       |\n"
        man += "    ———————\n"
        fmt = "```\n{}```".format(man)
        # Then just add the guesses and the blanks to the string
        fmt += "```\nGuesses: {}\nWord: {}```".format(", ".join(self.failed_letters), " ".join(self.blanks))
        return fmt


class Hangman:
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    def create(self, word, ctx):
        # Create a new game, then save it as the server's game
        game = Game(word)
        self.games[ctx.message.server.id] = game
        return game

    @commands.group(aliases=['hm'], pass_context=True, no_pm=True, invoke_without_command=True)
    @commands.cooldown(1, 30, BucketType.user)
    @checks.custom_perms(send_messages=True)
    async def hangman(self, ctx, *, guess):
        """Makes a guess towards the server's currently running hangman game"""
        game = self.games.get(ctx.message.server.id)
        if not game:
            ctx.command.reset_cooldown(ctx)
            await self.bot.say("There are currently no hangman games running!")
            return

        # Check if we are guessing a letter or a phrase. Only one letter can be guessed at a time
        # So if anything more than one was provided, we're guessing at the phrase
        # We're creating a fmt variable, so that we can  add a message for if a guess was correct or not
        # And also add a message for a loss/win
        if len(guess) == 1:
            if guess in game.guessed_letters:
                ctx.command.reset_cooldown(ctx)
                await self.bot.say("That letter has already been guessed!")
                # Return here as we don't want to count this as a failure
                return
            if game.guess_letter(guess):
                fmt = "That's correct!"
            else:
                fmt = "Sorry, that letter is not in the phrase..."
        else:
            if game.guess_word(guess):
                fmt = "That's correct!"
            else:
                fmt = "Sorry that's not the correct phrase..."

        if game.win():
            fmt += " You guys got it! The word was `{}`".format(game.word)
            del self.games[ctx.message.server.id]
        elif game.failed():
            fmt += " Sorry, you guys failed...the word was `{}`".format(game.word)
            del self.games[ctx.message.server.id]
        else:
            fmt += str(game)

        await self.bot.say(fmt)

    @hangman.command(name='create', aliases=['start'], no_pm=True, pass_context=True)
    @checks.custom_perms(send_messages=True)
    async def create_hangman(self, ctx):
        """This is used to create a new hangman game
        Due to the fact that I might not be able to delete a message, I will PM you and ask for the phrase you want.
        The phrase needs to be under 40 characters"""

        # Only have one hangman game per server, since anyone
        # In a server (except the creator) can guess towards the current game
        if self.games.get(ctx.message.server.id) is not None:
            await self.bot.say("Sorry but only one Hangman game can be running per server!")
            return

        game = self.create(phrases[random.SystemRandom().randint(0, len(phrases) - 1)], ctx)
        # Let them know the game has started, then print the current game so that the blanks are shown
        await self.bot.say(
            "Alright, a hangman game has just started, you can start guessing now!\n{}".format(str(game)))

    @hangman.command(name='delete', aliases=['stop', 'remove', 'end'], pass_context=True, no_pm=True)
    @checks.custom_perms(kick_members=True)
    async def stop_game(self, ctx):
        """Force stops a game of hangman
        This should realistically only be used in a situation like one player leaves
        Hopefully a moderator will not abuse it, but there's not much we can do to avoid that"""
        if self.games.get(ctx.message.server.id) is None:
            await self.bot.say("There are no Hangman games running on this server!")
            return

        del self.games[ctx.message.server.id]
        await self.bot.say("I have just stopped the game of Hangman, a new should be able to be started now!")


def setup(bot):
    bot.add_cog(Hangman(bot))
