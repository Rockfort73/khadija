import os
import re
import sys
import time
import json
import fbthon
import requests
import colorama
import webbrowser

sys.path.append('./lib/')

from botrawatfb import utils, RawatFb

if 'nt' not in os.name:
  import tty
  import termios
  colorama.init()

  reset = colorama.Fore.RESET # \033[1;0m
  red = colorama.Fore.RED # \033[1;91m
  green = colorama.Fore.GREEN # \033[1;92m
  yellow = colorama.Fore.YELLOW # {yellow}
  blue = colorama.Fore.BLUE # \033[1;94m
  magenta = colorama.Fore.MAGENTA # \033[1;95m
  cyan = colorama.Fore.CYAN # \033[1;96m
  white = colorama.Fore.WHITE # \033[1;97m
else:
  for color in ["reset","red","green","yellow","blue","magenta","cyan","white"]:
    globals()[color] = ""

garis = "{blue}──────────────────────────────────────────────────{reset}".format(blue = blue, reset = reset)
logo = "{garis}\n{yellow}  ▼￣＞-―-＜￣▼   {magenta}Author   {red}: {cyan}Rockfort\n{yellow}   Ｙ　     Ｙ    {magenta}Github   {red}: {cyan}https://github.com/Rockfort73\n{yellow}/\ /   {red}● {yellow}ω  {red}●{yellow}）   {magenta}CEO      {red}: {cyan}Asbulla|Afny|Khadijah'Karina'\n{yellow}\ ｜　 つ　  ヽつ {magenta}WhatsApp {red}: {cyan}6289521667925\n{blue}{garis}\n".format(garis = garis, blue = blue, yellow = yellow, magenta = magenta, red = red, cyan = cyan)
default_config = {"use_enter":False,"cookie_file":"./data/cookies.txt","font_folder":"./data/font/abeezee","image_folder":"./data/images/foto-post","background_folder":"./data/images/background","foto_profile":"./data/images/foto-frofile","2fa_file":"./data/2fa.json","cover_folder":"./data/images/cover-profile","account_pettern":"(.*?)\|\w{6,}","account_separator":"|","add_friend_suges_limit":5,"add_friends_post_limit":5,"acc_friend_limit":5,"like_post_beranda_limit":5,"comment_post_beranda_limit":5}

if not os.path.exists('./data'):os.mkdir('./data')
if not os.path.exists('./data/2fa.json'): open('./data/2fa.json','w').write(json.dumps({"Data":[]}))

try:
  config = json.load(open("./data/config.json"))
except (json.decoder.JSONDecodeError,FileNotFoundError):
  open('./data/config.json','w').write(json.dumps(default_config, indent = 2))
  config = default_config

try:
  cookies = open(config['cookie_file'],'r').readlines()
except FileNotFoundError:
  open(config['cookie_file'],'w').close()
  cookies = []

if len(open('./data/config.json','r').read()) <= 0:open('./data/config.json','w').write(json.dumps(default_config, indent = 2))

def clear():
  os.system('cls' if os.name == 'nt' else 'clear')

def getch():
  fd = sys.stdin.fileno()
  old_settings = termios.tcgetattr(fd)
  try:
    tty.setraw(sys.stdin.fileno())
    ch = sys.stdin.read(1)
  finally:
#    sys.stdin.flush()
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

  return ch

def delete_cookie(cookie, arrCookies = cookies):
  if cookie in arrCookies:
    del arrCookies[arrCookies.index(cookie)]

def getInput(text = ""):
  if config['use_enter'] or 'nt' in os.name:
    out = input(text)
  else:
    sys.stdout.write(text)
    sys.stdout.flush()
    out = getch()
    print (out)

  return out

def ketik(text, delay = 0.005, end = "\n", file = sys.stdout):
  for chr in text + end:
    file.write(chr)
    file.flush()
    time.sleep(delay)

def cekLicense(license):
  try:
    req = requests.get("https://rawatfbmanager.rahmadadha.repl.co/cek", data = {"license":license}).json()

    if req['error']:
      print ("{white}[{red}!{white}] {red}{err}".format(white = white, red = red, err = req['message']), file = sys.stderr)
    else:
      print ("{white}[{green}✓{white}] {msg}".format(white = white, green = green, msg = req['message']))

    return req['error']

  except Exception as err:
    print ("{white}[{red}!{white}] {red}{err}".format(white = white, red = red, err = err), file = sys.stderr)
    sys.exit(1)

def main():
  clear()
  ketik("{logo}{white}[{green}+{white}] Total Cookie: {green}{total_cookie}\n{garis}".format(logo = logo, white = white, green = green, total_cookie = len(cookies), garis = garis), delay = 0.003)
  try:
    pilih = int(getInput("{white}[{red}1{white}] Mulai Bot Facebook\n{white}[{red}2{white}] Tambahkan cookie Baru\n{white}[{red}3{white}] Cek Cookie\n{white}[{red}4{white}] {red}Hapus Semua Cookie\n{white}[{red}5{white}] Laporkan Bug\n{white}[{red}0{white}] Keluar\n{garis}\n{white}[{red}?{white}] Pilih : {cyan}".format(garis = garis, white = white, red = red, cyan = cyan)))

    if pilih == 1:
      print (garis)
      bot_post = getInput("{white}[{cyan}?{white}] Gunakan Bot Auto Create Post [Y/n] ".format(white = white, cyan = cyan)).lower() == "y"
      bot_share = getInput("{white}[{cyan}?{white}] Gunakan Bot Share Post [Y/n] ".format(white = white, cyan = cyan)).lower() == "y"

      if bot_share:
        sharePostUrl = input("{white}[{cyan}?{white}] Masukkan Link Post : ".format(white = white, cyan = cyan))

      bot_postText = getInput("{white}[{cyan}?{white}] Gunakan Bot Auto Create Post Teks [Y/n] ".format(white = white, cyan = cyan)).lower() == "y"
      add_suges = getInput("{white}[{cyan}?{white}] Gunakan Bot Auto Add Sugestion [Y/n] ".format(white = white, cyan = cyan)).lower() == "y"
      add_post = getInput("{white}[{cyan}?{white}] Gunakan Bot Auto Add From Post [Y/n] ".format(white = white, cyan = cyan)).lower() == "y"

      if add_post:
        while True:
          addPostUrl = input("{white}[{cyan}?{white}] Masukkan Link Post : ".format(white = white, cyan = cyan))
          if len (addPostUrl) > 0: break
          print ("{white}[{red}!{white}] Input tidak valid!".format(white = white, red = red))

      acc_friend = getInput("{white}[{cyan}?{white}] Gunakan Bot Auto Acc Friends [Y/n] ".format(white = white, cyan = cyan)).lower() == "y"
      like_beranda = getInput("{white}[{cyan}?{white}] Gunakan Bot Like Post Beranda [Y/n] ".format(white = white, cyan = cyan)).lower() == "y"
      comment_beranda = getInput("{white}[{cyan}?{white}] Gunakan Bot Comment Post Beranda [Y/n] ".format(white = white, cyan = cyan)).lower() == "y"
      tempat_asal = getInput("{white}[{cyan}?{white}] Gunakan Bot Update Kota asal [Y/n] ".format(white = white, cyan = cyan)).lower() == "y"
      kota_saatini = getInput("{white}[{cyan}?{white}] Gunakan Bot Update Kota saat ini [Y/n] ".format(white = white, cyan = cyan)).lower() == "y"
      update_profile = getInput("{white}[{cyan}?{white}] Gunakan Bot Update Profile Picture [Y/n] ".format(white = white, cyan = cyan)).lower() == "y"
      update_cover = getInput("{white}[{cyan}?{white}] Gunakan Bot Update Cover Profile [Y/n] ".format(white = white, cyan = cyan)).lower() == "y"
      enable2fa = getInput("{white}[{cyan}?{white}] Gunakan Bot enable 2FA [Y/n] ".format(white = white, cyan = cyan)).lower() == "y"
      ganti_password = getInput("{white}[{cyan}?{white}] Gunakan Bot Ganti Password [Y/n] ".format(white = white, cyan = cyan)).lower() == "y"
      update_mail = getInput("{white}[{cyan}?{white}] Gunakan Bot Update Email [Y/n] ".format(white = white, cyan = cyan)).lower() == "y"

      for akun in cookies:
        akun = akun.strip()
        if len(akun) <= 0: continue
        ketik(garis)
        try:
          if re.match(config['account_pettern'],akun):
            akunKu = akun.split(config['account_separator'])
            print ("{white}[{yellow}+{white}] Account : {white}\"{yellow}{akun}{white}\"{reset}".format(white = white, yellow = yellow, akun = akunKu[0], reset = reset))
            log = fbthon.login.Web_Login(akunKu[0],akunKu[1])
            rawat = RawatFb(log.get_cookie_str())
          else:
            fbid = re.search("c_user=(\d+)",akun)
            fbid = (fbid.group(1) if fbid is not None else None)
            print ("{white}[{yellow}+{white}] Account : {white}\"{yellow}{fbid}{white}\"{reset}".format(white = white, yellow = yellow, fbid = fbid, reset = reset))
            rawat = RawatFb(akun)

          if bot_post: rawat.update_status(config['image_folder'])
          if bot_share: rawat.shareToGroup(sharePostUrl)
          if bot_postText: rawat.update_statusText(background_folder = config['background_folder'], font_folder = config['font_folder'], caption = utils.randomDataXLSX('./data/kata-kata.xlsx'), text_color = (0,0,0))
          if add_suges: rawat.add_friends_suges(limit = config['add_friend_suges_limit'])
          if add_post: rawat.add_friends_post(post_url = addPostUrl, limit = config['add_friends_post_limit'])
          if acc_friend: rawat.acc_friends(limit = config['acc_friend_limit'])
          if like_beranda: rawat.like_post_beranda(limit = config['like_post_beranda_limit'])
          if comment_beranda: rawat.comment_post_beranda(limit = config['comment_post_beranda_limit'])
          if tempat_asal: rawat.updateHomeTown()
          if kota_saatini: rawat.updateCurrentCity()
          if update_profile: rawat.updateProfilePicture(config['foto_profile'])
          if update_cover: rawat.updateCoverProfile(config['cover_folder'])
          if enable2fa: rawat.enable2FA(config['2fa_file'])
          if ganti_password: rawat.gantiPassword()
          if update_mail: rawat.updateMail()

        except (fbthon.exceptions.InvalidCookies, ValueError, fbthon.exceptions.LoginFailed):
          print ("{white}[{red}!{white}] {red}Gagal login ke akun!{reset}".format(white = white, red = red,reset = reset), file = sys.stderr)
        except fbthon.exceptions.AccountCheckPoint:
          print ("{white}[{red}!{white}] {red}Akun terkena CheckPoint!{reset}".format(white = white, red = red,reset = reset), file = sys.stderr)
        except Exception as err:
          print ("{white}[{red}!{white}] {red}error {white}({red}{err}{white}){reset}".format(white = white, red = red,err = err,reset = reset), file = sys.stderr)
      else:
        ketik(garis)
        input("{white}[{green}Tekan Enter Untuk Kembali{white}]{reset}".format(white = white, green = green, reset = reset))
        main()
    elif pilih == 2:
      while True:
        total = getInput("{white}[{green}?{white}] Mau nambah berapa cookie? ".format(white = white, green = green))
        if total.isdigit() and int(total) > 0:
          break
        elif total.isdigit() and int(total) <= 0:
          print("{white}[{red}!{white}] {red}Minimal menambahkan 1 cookie".format(white = white, red = red))
          time.sleep(0.5)
        else:
          print("{white}[{red}!{white}] {red}Input tidak valid!!".format(white = white, red = red))
          time.sleep(0.5)
      for x in range(int(total)):
        try:
          ketik(garis)
          cookie = input("{white}[{green}+{white}] {cyan}Cookie {white}: {green}".format(white = white, green = green, cyan = cyan))
          id = re.search("c_user=(\d+)",cookie)
          id = (id.group(1) if id is not None else None)
          print ("{white}[{yellow}+{white}] Sedang login ke akun \"{cyan}{id}{white}\"".format(white = white, yellow = yellow, cyan = cyan, id = id))

          fbthon.login.Cookie_Login(cookie)
          print ("{white}[{green}✓{white}] Berhasil login ke akun \"{cyan}{id}{white}\"".format(white = white, green = green, id = id,cyan = cyan))
          file = open(config['cookie_file'],'a+')
          file.write((cookie + "\n"))
          file.close()
          print ("{white}[{green}+{white}] Status : Berhasil menambahkan cookie".format(white = white, green = green))
        except (fbthon.exceptions.InvalidCookies, ValueError):
          print ("{white}[{red}!{white}] Gagal login ke akun \"{cyan}{id}{white}\", cookie tidak valid".format(white = white, red = red, cyan = cyan, id = id), file = sys.stderr)
          print ("{white}[{red}!{white}] Status : Gagal menambahkan cookie".format(white = white, red = red), file = sys.stderr)
        except fbthon.exceptions.AccountCheckPoint:
          print ("{white}[{red}!{white}] Akun facebook \"{cyan}{id}{white}\" terkena {yellow}CHECKPOINT".format(white = white, red = red, cyan = cyan, id = id, yellow = yellow), file = sys.stderr)
          print ("{white}[{red}!{white}] Status : Gagal menambahkan cookie".format(white = white, red = red), file = sys.stderr)
        except Exception as err:
          print ("{white}[{red}!{white}] Error {white}({red}{err}{white})".format(white = white, red = red, err = err), file = sys.stderr)
          print ("{white}[{red}!{white}] Status : Gagal menambahkan cookie".format(white = white, red = red), file = sys.stderr)
      else:
        ketik(garis)
        input("{white}[{green}Tekan Enter Untuk Kembali{white}]{reset}".format(white = white, green = green, reset = reset))
        main()
    elif pilih == 3:
      delCok = getInput("{white}[{red}?{white}] Hapus Cookie yang sudah tidak valid? {white}[{green}Y{white}/{red}n{white}] {reset}".format(white = white, red = red, green = green, reset = reset)).lower() == 'y'
      print ("{white}[{yellow}+{white}] {cyan}Memulai Cek Cookie{reset}".format(white = white, yellow = yellow, cyan = cyan, reset = reset))
      ketik(garis)
      ok = 0
      cp = 0
      dead = 0
      for akun in cookies:
        try:
          if len(akun) <= 0:
            return
          elif re.match(config['account_pettern'],akun):
            myAccount = akun.split(config['account_separator'])
            print ("{white}[{green}+{white}] Account : {white}\"{cyan}{akun}{white}\"".format(white = white, green = green, akun = myAccount[0], cyan = cyan))
            fbthon.login.Web_Login(myAccount[0],myAccount[1].strip())
            print ("{white}[{green}✓{white}] Status  : {green}OK{reset}\n".format(white = white, green = green, reset = reset))
            ok += 1
          else:
            fbid = re.search("c_user=(\d+)",akun)
            fbid = (fbid.group(1) if fbid is not None else None)
            print ("{white}[{green}+{white}] Account : {white}\"{cyan}{fbid}{white}\"".format(white = white, green = green, cyan = cyan, fbid = fbid))
            fbthon.login.Cookie_Login(akun.strip())
            print ("{white}[{green}✓{white}] Status  : {green}OK{reset}\n".format(white = white, green = green, reset = reset))
            ok += 1
        except (fbthon.exceptions.InvalidCookies, ValueError, fbthon.exceptions.LoginFailed):
          print ("{white}[{red}!{white}] Status  : {red}DEAD{reset}\n".format(white = white, red = red, reset = reset), file = sys.stderr)
          if delCok: 
            delete_cookie(akun)
            open(config['cookie_file'],'w').write(''.join(cookies))
          dead += 1
        except fbthon.exceptions.AccountCheckPoint:
          print ("{white}[{red}!{white}] Status  : {yellow}CHECKPOINT{reset}\n".format(white = white,red = red, yellow = yellow, reset = reset), file = sys.stderr)
          if delCok:
            delete_cookie(akun)
            open(config['cookie_file'],'w').write(''.join(cookies))
          cp += 1
        except Exception as err:
          print ("{white}[{red}!{white}] Status  : {red}error {white}({red}{err}{white}){reset}\n".format(white = white, red = red, err = err, reset = reset), file = sys.stderr)
      else:
        ketik(garis)
        print ("{white}[{green}✓{white}] Total {green}OK   {white}: {green}{ok}{reset}".format(white = white, green = green, ok = ok,reset = reset))
        print ("{white}[{yellow}+{white}] Total {yellow}CP   {white}: {yellow}{cp}{reset}".format(white = white, yellow = yellow, cp = cp, reset = reset))
        print ("{white}[{red}!{white}] Total {red}DEAD {white}: {red}{dead}{reset}".format(white = white, red = red, dead = dead, reset = reset))
        input("\n{white}[{green}Tekan Enter Untuk Kembali{white}]{reset}".format(white = white, green = green, reset = reset))
        main()
    elif pilih == 4:
      yakin = getInput("{white}[{red}?{white}] Apakah anda ingin melanjutkan? {white}[{red}Y{white}/{green}n{white}] {reset}".format(white = white, red = red, green = green, reset = reset)).lower() == 'y'
      if yakin:
        open(config['cookie_file'],'w').close()
        print ("{white}[{green}✓{white}] {white}Berhasil Menghapus Cookie{reset}".format(white = white, green = green, reset = reset))
        sys.exit(0)
      else:
        main()
    elif pilih == 5:
      succes = webbrowser.open("https://wa.me/6285754629509")
      if not succes: os.system("xdg-open https://wa.me/6285754629509")
      time.sleep(1)
      main()
    elif pilih == 0:
      sys.exit("{white}[{red}!{white}] {yellow}Keluar!{reset}".format(white = white, red = red, yellow = yellow, reset = reset))
    else:
      print ("{white}[{red}!{white}] {red}Input tidak valid!{reset}".format(white = white, red = red,reset = reset))
      time.sleep(1)
      main()

  except ValueError:
    print ("{white}[{red}!{white}] {red}Input tidak valid!{reset}".format(white = white, red = red,reset = reset))
    time.sleep(1)
    main()


if __name__ =="__main__":
  print("{white}[{red}!{white}] Tunggu Sebentar".format(white = white, red = red))
  if os.path.exists("./data/license.txt"):
    cek = cekLicense(open("./data/license.txt","r").read().strip())
    if cek: os.unlink("./data/license.txt")
  else:
    clear()
    license = input("{logo}\r{white}[{red}?{white}] {cyan}Masukkan LICENSE {white}: {cyan}".format(logo = logo,white = white, red = red, cyan = cyan))
    cek = cekLicense(license)
    if not cek: open("./data/license.txt","w").write(license)
  if not cek:
    ketik ("{white}[{green}!{white}] Selamat Datang".format(white = white, green = green))
    time.sleep(1)
    main()
  else:
    sys.exit(1)
else:
  del main
