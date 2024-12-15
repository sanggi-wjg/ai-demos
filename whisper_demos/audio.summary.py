from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

transcript = """
하지만 오늘 슈퍼챗이.. 슈퍼챗이 막 터지고 있어요? 나한테 들어오는 것도 아닌데.. 슈퍼챗이 오늘 왜 이렇게 잘 터져요? 여러분 감사합니다. 나랑 문헌 아니야? 아니 그래도.. 읽어줘야 된다고.. 어디서 보니까 슈퍼챗을 읽어줘야 된다고 하거든요? 원래는 그런데 우리 수사장님의.. 슈퍼챗 전화! 여러분 슈퍼챗 전화를 하는 게 아니고.. 그만 그만 그만.. 돈이 문제가 아니라.. 외롭거든요. 
욕을 먹으면 외로워. 많이 옆에 있어 주시면 좋을 것 같아요. 구독 취소한 양반들 다시 구독 눌러. 취소 많이 하셨더라고요. 어차피 다시 할까? 알려라. 어차피 돌아와요 여러분. 다른 데 봐도 똑같아. 그러니까. 아니 지금 다 뉴스에서 힘들고 어려운데 사실 지금 너무나 진지하고 중요한 시점인 건 맞지만 또 저희는 저희 채널의 나름대로의 컨텐츠를 이어나가 보도록 하겠습니다. 
그래서 제가 오늘 이제 돈 벌 수 있는 걸 자주 왔죠. 그렇죠. 왜냐하면 이 와중에 어차피 내일 표결 끝날 때까지 우리가 할 수 있는 게 지금은 없어. 그냥 유튜브 보고 다음 주 월요일에 뭘 사야 되는지 이런 것들 얼마나 사야 되는지 그런 걸 말씀을 드리려고 왜냐하면 이 시점에도 또 돈 버는 사람들도 있고 그러니까 또 이 나라의 정치와 경제는 또 연결이 되어 있지 않습니까? 정치도 정치지만 
거기 정치에서 또 우리 지금 경제도 안 좋은데 우리 지금 오는 코스다 666 드디어 깨졌거든요? 그 얘기도 해야 되고 사실 경제도 매우 중요하죠. 자랑해야 되는데 분위기가 이래가지고 봤죠? 내가 그랬죠? 내가 빠진다고 했지? 계속 했잖아 그죠? 근데 맨날 뭐 멍마친다고 막 그러고 비웃다가 이제 와서 자랑할 때 되니까 분위기가 이러네. 어 없어졌어. 아니 근데 666에 깨지고 반등한다고 하셨거든요? 
데드캡 바운스로 666 찍고 올라온다고 했는데 666 찍고? 그랬나 내가? 다시 또 지어가던데'
""".strip()

llm = ChatOllama(
    model="exaone3.5:7.8b",
    temparature=0,
)
prompt = ChatPromptTemplate.from_template(
    "Summarize the following audio transcript. Consider that there are some strange changes to audio conversion text. Ensure that all answers are in Korean.\nTranscript:{transcript}\nSummary:"
)
chain = prompt | llm | StrOutputParser()

for token in chain.stream({'transcript': transcript}):
    print(token, end="", flush=True)
