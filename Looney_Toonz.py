import random
import threading

PLAYER_INFO = [
            ("Bugs Bunny","B", "None", True, False, False), 
            ("Tweety Bird","T", "None", True, False, False), 
            ("Tazmanian Devil", "D", "None", True, False, False)
            ("Marvin Martian", "M", "Shoot", True, False, False)
            ]


class Player:

    #Ability = Marvin being able to kill other players
    #Status: Alive = True, Dead = False
    def __init__(self, playerName, playerSymbol, playerAbility, status, hasFlag, hasWin):
        self.name = playerName
        self.symbol = playerSymbol
        self.ability = playerAbility
        self.isAlive = status
        self.hasFlag = hasFlag
        self.winner = hasWin

#Define getters and setters
    def getName(self):
        return self.name

    def getSymbol(self):
        return self.symbol

    def getStatus(self):
        return self.isAlive

    def getFlag(self):
        return self.hasFlag
    
    def getWin(self):
        return self.winner

    def setStatus(self, status):
        self.isAlive = status

    def setFlag(self, hasFlag):
        self.hasFlag = hasFlag
    
    def setWin(self, hasWin):
        self.winner = hasWin
