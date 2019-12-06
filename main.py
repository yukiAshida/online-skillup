import random
import time
import json, os
import traceback
import urllib

MEMORY_FILE = "memory.json"
TOKEN = "yIaWH8Uiatv7tYkmonVddsHWOb4yt4Ax"

class Client():
    """
    ・短いメッセージを送り、返ってきた得点をひたすら記録
    ・時々、高い得点のメッセージを組み合わせて、高得点を狙う
    ・中断しても最初からにならないように、毎回ファイルに書き出し
    ・強化学習のように行動に対する価値を更新するべき？
    ・行動の種類が絞れない？time intervalがあるため、学習が回りきらない？
    ・強化学習の知見が足りない。。
    """

    def __init__(self):

        # メッセージと得点の記録用辞書
        self.memory = {}

        # 記録用ファイルが存在する場合のみファイルの読み込みを行う
        if os.path.exists(MEMORY_FILE):
            self.readJson()

        # 管理する点数帯の幅
        self.width = 50
    
    def writeJson(self, filepath=MEMORY_FILE):
        """ メッセージと得点を記録した辞書をjsonに書き出す関数 """

        f = open(filepath, "w", encoding="utf-8")
        json.dump(self.memory, f, indent=2, ensure_ascii=False)
        f.close()
        print("Wrote memory file.")

    def readJson(self, filepath=MEMORY_FILE):
        """ メッセージと得点を記録したjsonを読み込む関数 """

        f = open(filepath, "r")
        self.memory.update(json.load(f))
        f.close()
        print("Read memory file.")    
    
    def makeLabel(self, point):
        """
        与えられた得点がどの得点帯に属するかを返す関数

        Parameters
        ------------
            point: int

        Returns
        ------------
            得点帯を表すstr
            ex) "100-150"
        """

        return "{0}-{1}".format( str(point//self.width*self.width), str((point+self.width)//self.width*self.width) )

    def hasMessage(self, message):
        """
        メッセージが辞書に記録されているか判断する関数

        Parameters
        ------------
            message: str

        Returns
        ------------
            tupple
                0. bool値（メッセージを既に記録しているか）
                1. int (メッセージを記録している場合はその得点、記録していない場合は0)
        """

        # 各得点帯を調査
        for data in self.memory.values():

            # 既にメッセージを持っている場合
            if message in data.keys():
                return True, data[message]
        
        return False, 0

    def sendMessage(self, message, memory=True):
        """
        メッセージを送信する

        Parameters
        ------------
            message: str
            token: str
            memory: bool
                送信したメッセージと得られた得点を辞書に登録するかどうか

        Returns
        ------------
            int
                得られた得点（ただし、既に送信していた場合は登録されていた得点を返す）
        """

        # 既にその単語を調べている場合は送信を行わない    
        judge, point = self.hasMessage(message)
        if judge:
            return point

        # httpリクエストを行う
        url = "https://runner.team-lab.com/q?token={0}&str={1}".format(TOKEN, message)
        res = urllib.request.urlopen(url)
        point = int(res.read().decode("utf-8"))
        
        # 送った値を記録しておく場合
        if memory:

            # 得点に応じて、得点帯ラベルを生成
            label = self.makeLabel(point)

            # その点数帯が初めてであれば辞書に新しく登録
            if not label in self.memory:
                self.memory[label] = {}
            
            # 得点を記録                
            self.memory[label][message] = point

        # リクエストの間隔調整
        time.sleep(1)

        return point

    def randomMessage(self, n):
        """ ランダムなn文字のメッセージを作成する """

        return "".join([ random.choice(["A","B","C","D"]) for _ in range(n) ])

    def generateMemory(self):
        """ 辞書を充実させるための処理 """

        # ランダムな8文字の文字列を生成
        message = self.randomMessage(8)

        # メッセージを送信
        point = self.sendMessage(message)

        return message, point

    def aimHighScore(self, n_high=3):
        """ 高得点を狙うための処理 """
        
        # 最高得点帯のラベルを上位n_high個取り出す（得点ラベルがソートされていない）
        labels = list(self.memory.keys())
        labels_sorted = sorted([(int(label.split("-")[0]),label) for label in labels])
        high_labels = [ label for _, label in labels_sorted ][-n_high:]

        # 高得点帯のメッセージをリストに集計する
        high_scores = []
        for hl in high_labels:
            high_scores += list(self.memory[hl].keys())

        # 高得点メッセージを組み合わせる
        random.shuffle(high_scores)
        message = "".join( high_scores )[:50]

        # 50文字以下なら乱数で生成
        if len(message) < 50:
            message += self.randomMessage(50-len(message))

        # メッセージを送信
        point = self.sendMessage(message, memory=False)
        print(f"message={message}, point={point}")        
        
        return message, point
    
    def run(self, n_memory=10, n_score=1):
        """ 
        ループ関数 
        
        Parameters
        --------------
        n_memory: int
            1ループでgenerateMemory関数を呼び出す回数
        n_score: int
            1ループでaimHighScore関数を呼び出す関数
        """
        
        try:
            while True:
                
                # 辞書を増やす
                for _ in range(n_memory):
                    self.generateMemory()
                
                # 登録された情報から高得点を狙う
                for _ in range(n_score):
                    self.aimHighScore()

        except:
            traceback.print_exc()
            self.writeJson()

if __name__ == "__main__":

    client = Client()
    client.run(n_memory=10, n_score=1)


    
