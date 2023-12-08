import os
import re
import sys
import json
import random
import tempfile
import colorama

from . import utils
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.parse import urlparse
from fbthon import Facebook,settings
from fbthon import utils as fbthonUtils

from PIL import Image, ImageDraw, ImageFont, ImageOps

colorama.init()

reset = colorama.Fore.RESET
red = colorama.Fore.RED
green = colorama.Fore.GREEN
yellow = colorama.Fore.YELLOW
blue = colorama.Fore.BLUE
magenta = colorama.Fore.MAGENTA
cyan = colorama.Fore.CYAN
white = colorama.Fore.WHITE

class RawatFb(Facebook):
  PULAU_INDONESIA = ["Papua","Kalimantan","Sumatera","Sulawesi","Jawa","Bengkulu","Riau","Jambi","Lampung","Banten","DKI Jakarta","Daerah Istimewa Yogyakarta","Nusa Tenggara","Gorontalo","Bali","Bangka Belitung","Nanggroe Aceh Darussalam","Kepulauan Riau","Maluku"]

  def __init__(self, cookies):
    super().__init__(cookies)
    self.host = self._Facebook__host
    self.session = self._Facebook__session
    if 'Host' in self.session.headers.keys(): del self.session.headers['Host']

  def __get_profile_hovercard(self, TAG):
    profile = TAG.find_next('a', href = re.compile('\/friends\/hovercard\/mbasic'))
    nama = profile.text
    username =re.search('\/friends\/hovercard\/mbasic\/\?uid=(\d+)',profile['href']).group(1)

    return {"name":nama,"username":username}

  def __wrap_text(self, draw, text, font, max_width):
    lines = []
    words = text.split()
    current_line = ""

    for word in words:
      test_line = current_line + word + " "
      text_width, _ = draw.textsize(test_line, font=font)

      if text_width <= max_width:
        current_line = test_line
      else:
        lines.append(current_line)
        current_line = word + " "

    lines.append(current_line)

    return lines

  def __getPostBeranda(self, limit):
    postList = []

    for post in BeautifulSoup(self.session.get(urljoin(self.host,'/')).content,'html.parser').findAll('div', attrs = {'role':'article','data-ft':True}):
      if len(postList) >= limit: break
      ft_data = json.loads(post.get('data-ft'))
      author = post.find('a', attrs = {'class':'author-link'})
      if author is None:author = post.find('a')
      caption  = [khaneysia_nabila_zahra.text for khaneysia_nabila_zahra in post.findAll('p')]
      upload_time = post.find('abbr')
      action_like = post.find('a', href = re.compile('^\/a\/like\.php'))
      post_url = post.find("a", href = re.compile("^\/story\.php"))

      author = (author.text if author is not None else None)
      caption = ('\n'.join(caption) if len(caption) != 0 else '')
      upload_time = (upload_time.text if upload_time is not None else None)
      action_like = (urljoin(self.host,action_like['href']) if action_like is not None else None)
      post_url = (urljoin(self.host,post_url['href']) if post_url is not None else None)

      postList.append({"author":author,"caption":caption,"upload_time":upload_time,"action_like":action_like,"post_url":post_url})

    return postList


  def __updateTempatTinggal(self, edit, tempat):
    html = BeautifulSoup(self.session.get(urljoin(self.host,"/me?v=info")).content,'html.parser')
    edit_url = html.find("a", href = re.compile("^\/editprofile\.php\?(.*)edit=%s" % (edit)))
    response = {"status":None, "from": None, "to":None}

    if edit_url is not None:
      edit_html = BeautifulSoup(self.session.get(urljoin(self.host, edit_url['href'])).content,'html.parser')
      form = edit_html.find("form", action = re.compile("^\/a\/editprofile\.php\?"))

      if form is not None:
        data = {"save":"submit"}
        for inp in form.findAll("input", attrs = {"type":"hidden"}): data.update({inp['name']:inp['value']})
        inpTempat = form.find("input", attrs = {"type":"text"})

        try:
          if len(str(inpTempat['value'])) > 0: response['from'] = inpTempat['value']
        except KeyError:
          pass

        data[inpTempat['name']] = tempat
        formConfirm = BeautifulSoup(self.session.post(urljoin(self.host,form['action']), data = data).content,'html.parser').find("form", action = re.compile("^\/a\/editprofile\.php\?"))
        formSelect = formConfirm.find("select")

        if formSelect is not None:
          formConfirmData = {i['name']:i['value'] for i in formConfirm.findAll('input', attrs = {'type':'hidden'})}
          formConfirmData['save'] = 'submit'
          options = {i.text:i['value'] for i in formConfirm.findAll("option")}
          tempatBaru = random.choice(list(options.keys()))
          formConfirmData[formSelect['name']] = options[tempatBaru]
          confirm = self.session.post(urljoin(self.host,formConfirm['action']), data = formConfirmData)
          response['status'] = (True if confirm.ok else False)
          response['to'] = tempatBaru

    return response

  def __getGroups(self, limit = 3):
    html = BeautifulSoup(self.session.get(urljoin(self.host,"groups")).content,'html.parser')
    mygroup = []

    for group in html.findAll("a", href = re.compile("\/groups\/\d+")):
      try:
        if group.find_previous('tr').find('a', href = re.compile('\/a\/group\/join')) is not None: continue
        mygroup.append({"name":group.text,"url":group['href']})
      except AttributeError:
        continue

    return mygroup[0:limit]

  def __addEmail(self, newEmail):
    html = BeautifulSoup(self.session.get(urljoin(self.host,"/settings/email")).content,'html.parser')
    addUrl = html.find("a", href = re.compile("^\/settings\/email\/add"))

    if addUrl is not None:
      html = BeautifulSoup(self.session.get(urljoin(self.host,addUrl['href'])).content,'html.parser')
      form = html.find("form", action = re.compile("^\/a\/settings\/email"))
      data = {i['name']:i['value'] for i in form.findAll('input', attrs = {'type':'hidden','name':True,'value':True})}
      data['email'] = newEmail
      data['save'] = form.find('input', attrs = {'name':'save'}).get('value')
      submit = self.session.post(urljoin(self.host,form['action']), data = data)
      submitRes = BeautifulSoup(submit.content,'html.parser')
      if 'email/add' in submit.url:
        print (f"{white}[{red}!{white}] {red}{submitRes.find('div', attrs = {'id':'root'}).find('span').text}")
        return False
      else:
        print (f"{white}[{green}✓{white}] Berhasil menambahkan email")
        return True

  def __confirmEmail(self):
    html = BeautifulSoup(self.session.get(urljoin(self.host,"/settings/email")).content,'html.parser')
    confirmUrl = html.find("a", href = re.compile("^\/entercode\.php"))

    if confirmUrl is not None:
      html = BeautifulSoup(self.session.get(urljoin(self.host,confirmUrl['href'])).content,'html.parser')
      form = html.find("form", action = re.compile("^\/entercode\.php"))
      data = {i['name']:i['value'] for i in form.findAll('input', attrs = {'type':'hidden','name':True,'value':True})}
      email = form.find_previous('b').text
      print (f"{white}[{yellow}+{white}] {yellow}Masukkan Kode Konfirmasi yang sudah di kirim ke {white}\"{email}\"")
      print (f"{white}[{yellow}+{white}] {yellow}Kamu punya 3 kesempatan untuk memasukkan kode!\n")

      for i in range(3):
        data['code'] = input(f"{white}[{red}?{white}] Masukkan Kode : {cyan}")
        submit = self.session.post(urljoin(self.host,form['action']), data = data)
        submitRes = BeautifulSoup(submit.content,'html.parser')

        if 'entercode' in submit.url:
          print (f"{white}[{red}!{white}] {red}{submitRes.find('div', attrs = {'id':'root'}).find('span').text}")
        else:
          print (f"{white}[{green}✓{white}] {green}Berhasil Mengkonfirmasi email")
          return True
      else:
        return False

  def __updatePrimaryMail(self, email):
    html = BeautifulSoup(self.session.get(urljoin(self.host,"/settings/email")).content,'html.parser')
    primaryUrl = html.find("a", href = re.compile("\/email(?:\/\?|\?)primary_email"))

    if primaryUrl is not None:
      html = BeautifulSoup(self.session.get(primaryUrl['href']).content,'html.parser')
      form = html.find('form', action = re.compile('^\/a\/settings\/email'))
      data = {i['name']:i['value'] for i in form.findAll('input', attrs = {'type':'hidden','name':True,'value':True})}
      emailList = [i.text for i in form.findAll('label')]
      data['email'] = str(emailList.index(email))
      data['save'] = form.find('input', attrs = {'name':'save'}).get('value')
      submit = self.session.post(urljoin(self.host,form['action']), data = data)
      print (f"{white}[{green}✓{white}] Berhasil memperbarui email utama")

      return True

  def __deleteEmail(self):
    html = BeautifulSoup(self.session.get(urljoin(self.host,"/settings/email")).content,'html.parser')
    removeUrl = html.find('a', href = re.compile('^\/settings\/email(?:\/\?|\/)remove_email'))

    if removeUrl is not None:
      html = BeautifulSoup(self.session.get(urljoin(self.host,removeUrl['href'])).content,'html.parser')
      form = html.find('form', action = re.compile('\/a\/settings\/email'))
      data = {i['name']:i['value'] for i in form.findAll('input', attrs = {'type':'hidden','name':True,'value':True})}
      data['save'] = form.find('input', attrs = {'name':'save'}).get('value')
      print (f"{white}[{yellow}+{white}] {yellow}Masukkan Kata Sandi Facebook")
      print (f"{white}[{yellow}+{white}] {yellow}Kamu punya 3 kesempatan untuk memasukkan kata sandi\n")
      for i in range(3):
        password = input(f"{white}[{red}?{white}] Password : ")
        data['save_password'] = password
        submit = self.session.post(urljoin(self.host,form['action']), data = data)
        submitRes = BeautifulSoup(submit.content,'html.parser')
        nextForm = submitRes.find('form', action = re.compile('\/password\/reauth'))

        if nextForm is not None:
          nextData = {i['name']:i['value'] for i in nextForm.findAll('input', attrs = {'type':'hidden','name':True,'value':True})}
          nextData['save'] = nextForm.find('input', attrs = {'name':'save'}).get('value')
          for x in range(3):
            nextData['pass'] = password
            submit = self.session.post(nextForm['action'], data = nextData)
            submitRes = BeautifulSoup(submit.content,'html.parser')
            if 'password/reauth' in submit.url:
              print (f"{white}[{red}!{white}] {red}Kata Sandi Tidak Valid!")
              password = input(f"{white}[{red}?{white}] Password : ")
            else:
              print (f"{white}[{green}✓{white}] Berhasil menghapus email")
              break
          break
        elif 'remove_email' in submit.url:
          print (f"{white}[{red}!{white}] {red}Kata Sandi Tidak Valid!")
        else:
          print (f"{white}[{green}✓{white}] Berhasil menghapus email")
          break

  def update_status(self, img_folder):
    print("{white}[{yellow}+{white}] Membuat Postingan{reset}".format(white = white, yellow = yellow, reset = reset))
    img_file = utils.getFilesWithExtension(img_folder, [".jpg",".png",".jpeg"])

    if len(img_file) <= 0:
      print("{white}[{red}!{white}] {yellow}Tidak ada Foto di dalam folder {white}\"{cyan}{folder}{white}\"{reset}".format(white = white, red = red, yellow = yellow, cyan = cyan, folder = os.path.basename(img_folder), reset = reset))
    else:
      random_img = random.choice(img_file)
      jam = datetime.now().hour

      if jam >= 4 and jam < 12:
        caption = "Selamat Pagi"
      elif jam >= 12 and jam <= 15:
        caption = "Selamat Siang"
      elif jam > 15 and jam <= 18:
        caption = "Selamat Sore"
      else:
        caption = "Selamat Malam"

      caption += random.choice([" semuanya"," ganteng"," kalian"])

      sukses = self.create_timeline(target = 'me', message = caption, file = random_img, feeling = "Happy")

      if sukses:
        print("{white}[{green}✓{white}] {green}Berhasil membuat status{reset}\n".format(white = white, green = green,reset = reset))
      else:
        print("{white}[{yellow}!{white}] {red}Gagal membuat status{reset}\n".format(white = white, yellow = yellow, red = red, reset = reset), file = sys.stderr)

  def update_statusText(self, background_folder, font_folder, caption, text_color = (255, 255, 255)):
    print("{white}[{yellow}+{white}] Membuat Postingan Teks{reset}".format(white = white, yellow = yellow, reset = reset))
    img_file = utils.getFilesWithExtension(background_folder, [".jpg",".png",".jpeg"])
    font_path = utils.findFristFileExtension(font_folder, [".otf",".ttf"])

    if len(img_file) <= 0:
      print("{white}[{red}!{white}] {yellow}Tidak ada Foto di dalam folder {white}\"{cyan}{folder}{white}\"{reset}".format(white = white, red = red, yellow = yellow, cyan = cyan, folder = os.path.basename(background_folder), reset = reset))
    elif font_path is None:
      print("{white}[{red}!{white}] {yellow}Font {white}\"{yellow}{fonts}{white}\"{reset}".format(white = white, red = red, yellow = yellow, fonts = os.path.basename(font_folder), reset = reset))
    elif len(caption) < 1:
      print("{white}[{red}!{white}] {yellow}Panjang caption minimal 1 karakter{reset}".format(white = white, red = red, yellow = yellow, reset = reset))
    else:
      temp = tempfile.NamedTemporaryFile(mode = 'w', suffix='.jpg', delete = False)
      temp.close()
      tempImg = open(temp.name,'w')
      image = Image.open(random.choice(img_file))
      draw = ImageDraw.Draw(image)
      width, height = image.size
      font_size_percentage = 0.10
      font_size = int(min(width, height) * font_size_percentage)
      font = ImageFont.truetype(font_path, font_size)
      wrapped_text = self.__wrap_text(draw, caption, font, width)
      total_text_height = len(wrapped_text) * font.getsize(wrapped_text[0])[1]
      y = (height - total_text_height) // 2

      for line in wrapped_text:
        text_width, text_height = draw.textsize(line, font=font)
        x = (width - text_width) // 2
        draw.text((x, y), line, fill=text_color, font=font)
        y += text_height
      else:
        image.save(temp.name)
        image.close()
        sukses = self.create_timeline(target = 'me', message = "", file = temp.name)

        if sukses:
         print("{white}[{green}✓{white}] {green}Berhasil membuat status{reset}\n".format(white = white, green = green,reset = reset))
        else:
         print("{white}[{yellow}!{white}] {red}Gagal membuat status{reset}\n".format(white = white, yellow = yellow, red = red, reset = reset), file = sys.stderr)

      tempImg.close()
      os.unlink(temp.name)

  def updateHomeTown(self, city = None):
    print ("{white}[{yellow}+{white}] Memperbarui Tempat Asal".format(white = white, yellow = yellow))
    if city is None: city = random.choice(self.PULAU_INDONESIA)
    ganti = self.__updateTempatTinggal("hometown", city)

    if ganti['status']:
      print ("{white}[{green}✓{white}] Berhasil Memperbarui Tempat Asal".format(white = white, green = green))
      print ("{white}[{green}✓{white}] {pesan}\n".format(white = white, green = green, pesan = ("%s\"%s%s%s\" ---> \"%s%s%s\"" % (white,red,ganti['from'],white, green, ganti['to'], white) if ganti['from'] else ganti['to'])))
    else:
      print ("{white}[{red}!{white}] Gagal Memperbarui Tempat Asal\n".format(white = white, red = red))

  def updateCurrentCity(self, city = None):
    print ("{white}[{yellow}+{white}] Memperbarui Kota Saat Ini".format(white = white, yellow = yellow))
    if city is None: city = random.choice(self.PULAU_INDONESIA)
    ganti = self.__updateTempatTinggal("current_city", city)

    if ganti['status']:
      print ("{white}[{green}✓{white}] Berhasil Memperbarui Kota Saat Ini".format(white = white, green = green))
      print ("{white}[{green}✓{white}] {pesan}\n".format(white = white, green = green, pesan = ("%s\"%s%s%s\" ---> \"%s%s%s\"" % (white,red,ganti['from'],white, green, ganti['to'], white) if ganti['from'] else ganti['to'])))
    else:
      print ("{white}[{red}!{white}] Gagal Memperbarui Kota Saat Ini\n".format(white = white, red = red))

  def updateProfilePicture(self, image_folder):
    print("{white}[{yellow}+{white}] Memulai Bot Update Profile Picture{reset}".format(white = white, yellow = yellow, reset = reset))
    img = utils.getFilesWithExtension(image_folder, ['.jpg','.jpeg','.png'])

    if len(img) <= 0:
      print ("{white}[{red}!{white}] Tidak ada foto di dalam folder {white}\"{yellow}{folder}{white}\"\n".format(white = white, red = red, yellow = yellow, folder = os.path.basename(image_folder)))
    else:
      if settings.UpdateProfilePicture(self, random.choice(img)):
        print ("{white}[{green}✓{white}] Berhasil memperbarui foto profile".format(white = white, green = green))
      else:
        print("{white}[{red}!{white}] {yellow}Gagal mengganti foto profile{reset}\n".format(white = white, red = red,yellow = yellow,reset = reset))

  def updateCoverProfile(self, image_folder):
    print("{white}[{yellow}+{white}] Memulai Bot Update Cover Profile{reset}".format(white = white, yellow = yellow, reset = reset))
    img = utils.getFilesWithExtension(image_folder, ['.jpg','.jpeg','.png'])

    if len(img) <= 0:
      print ("{white}[{red}!{white}] Tidak ada foto di dalam folder {white}\"{yellow}{folder}{white}\"\n".format(white = white, red = red, yellow = yellow, folder = os.path.basename(image_folder)))
    else:
      photo = random.choice(img)
      updateCoverUrl = BeautifulSoup(self.session.get(urljoin(self.host,'/me')).content,'html.parser').find('a', href = re.compile('^\/cover_photo'))
      if updateCoverUrl is not None:
        uploadUrl = BeautifulSoup(self.session.get(urljoin(self.host,updateCoverUrl['href'])).content,'html.parser').find('a', href = re.compile('^\/photos\/upload'))
        if uploadUrl is not None:
          uploadForm = BeautifulSoup(self.session.get(urljoin(self.host,uploadUrl['href'])).content,'html.parser').find('form', action = re.compile('^\/timeline\/cover\/upload'))
          if uploadForm is not None:
            data = {}
            for inp in uploadForm.findAll("input", attrs = {"type":"hidden"}):
              try:
                data[inp['name']] = inp['value']
              except KeyError:
                continue
            else:
              upload = fbthonUtils.upload_photo(requests_session = self.session, upload_url = urljoin(self.host,uploadForm['action']), input_file_name = 'file1', file_path = photo, fields = data)
              if upload.ok:
                print ("{white}[{green}✓{white}] Berhasil memperbarui foto sampul".format(white = white, green = green))
              else:
                print("{white}[{red}!{white}] {yellow}Gagal mengganti foto sampul{reset}\n".format(white = white, red = red,yellow = yellow,reset = reset))
          else:
            print("{white}[{red}!{white}] {yellow}Tidak dapat mengupload photo{reset}\n".format(white = white, red = red,yellow = yellow,reset = reset))
        else:
          print("{white}[{red}!{white}] {yellow}Gagal mengupload photo:({reset}\n".format(white = white, red = red,yellow = yellow,reset = reset))
      else:
        print("{white}[{red}!{white}] {yellow}Tidak dapat mengganti foto sampul:({reset}\n".format(white = white, red = red,yellow = yellow,reset = reset))

  def enable2FA(self, saveTo):
    print("{white}[{yellow}+{white}] Memulai Mengaktifkan 2FA pada akun{reset}".format(white = white, yellow = yellow, reset = reset))
    html = BeautifulSoup(self.session.get(urljoin(self.host,'security/2fac/setup/intro/metadata?source=1')).content,'html.parser')
    url = html.find("a", href = re.compile("(.*)\/security\/2fac\/setup\/qrcode\/generate\/\?"))
    if url is not None:
      form2FA = BeautifulSoup(self.session.get(url['href']).content,'html.parser').find("form", action = re.compile("^\/security\/2fac\/setup"))
      if form2FA is not None:
        form2FAData = {i['name']:i['value'] for i in form2FA.findAll('input', attrs = {'type':'hidden'})}
        kode2FA = form2FA.find('div', string = re.compile('(?:\w{4}\s){7,}'))
        if kode2FA is not None:
          print ("{white}[{green}+{white}] Masukkan kode \"{green}{kode}{white}\" pada aplikasi 2FA".format(white = white, green = green,kode = kode2FA.text))
          print ("{white}[{green}+{white}] Kamu punya 3 kesempatan untuk memasukkan kode verifikasi".format(white = white, green = green))
          confirmForm = BeautifulSoup(self.session.post(urljoin(self.host,form2FA['action']), data = form2FAData).content,'html.parser').find("form", id = "input_form")
          confirmData = {i['name']:i['value'] for i in confirmForm.findAll('input', attrs = {'type':'hidden'})}
          confirmData['submit_code_button'] = 'submit'

          for x in range(3):
            confirmData['code'] = input("{white}[{cyan}?{white}] Masukkan kode : {cyan}".format(white = white, cyan = cyan))
            confirmSubmit = BeautifulSoup(self.session.post(urljoin(self.host, confirmForm['action']), data = confirmData).content,'html.parser')
            pesanError = confirmSubmit.find("span", id = "type_code_error")

            if pesanError is not None:
              print ("{white}[{red}!{white}] {yellow}{pesan}".format(white = white, red = red,yellow = yellow, pesan = pesanError.text), file = sys.stderr)
            else:
              print ("{white}[{green}✓{white}] Berhasil mengaktifkan 2FA".format(white = white, green = green))
              data = json.load(open(saveTo,'r'))

              if 'Data' in data:
                data['Data'].append({"account":self.get_cookie_dict()['c_user'],"2FA":kode2FA.text})
                with open(saveTo,'w') as file:
                  file.write(json.dumps(data, indent = 3))

              break
        else:
          print("{white}[{red}!{white}] {yellow}Gagal mendapatkan kode 2FA :({reset}\n".format(white = white, red = red,yellow = yellow,reset = reset))
      else:
        print("{white}[{red}!{white}] {yellow}Tidak dapat mengaktifkan 2FA{reset}\n".format(white = white, red = red,yellow = yellow,reset = reset))
    else:
      print("{white}[{red}!{white}] {yellow}Tidak dapat mengaktifkan 2FA{reset}".format(white = white, red = red,yellow = yellow,reset = reset))
      print("{white}[{red}!{white}] {yellow}2FA Mungkin sudah aktif pada akun ini{reset}\n".format(white = white, red = red,yellow = yellow,reset = reset))

  def add_friends_post(self, post_url, limit = 5):
    print("{white}[{yellow}+{white}] Memulai Bot Add Friends From Post{reset}".format(white = white, yellow = yellow, reset = reset))
    post = self.post_parser(post_url)
    react = []

    for i in post.get_react_with_user(limit = limit).values():
      if len(react) >= limit:break
      react.extend(i['user'])

    if len(react) < 1:
      print ("{white}[{red}!{white}] Tidak ada react pada post ini!\n".format(white = white, red = red, yellow = yellow))
    else:
      print("")
      print ("{white}[{green}+{white}] Author  : {nama}".format(white = white, green = green, nama = post.author))
      print ("{white}[{green}+{white}] Upload  : {upload}".format(white = white, green = green, upload = post.upload_time))
      print ("{white}[{green}+{white}] Post Url: {url}".format(white = white, green = green, url = post.post_url), end = "\n\n")

      for user in react[0:limit]:
        try:
          if self.add_friends(user['username']):
            print ("{white}[{green}+{white}] Nama akun: {nama}".format(white = white, green = green, nama = user['name']))
            print ("{white}[{green}+{white}] ID Akun  : {username}".format(white = white, green = green, username = user['username']))
            print ("{white}[{green}✓{white}] Status   : Sukses\n".format(white = white, green = green))
          else:
            print ("{white}[{yellow}+{white}] Nama akun: {nama}".format(white = white, yellow = yellow, nama = user['name']))
            print ("{white}[{yellow}+{white}] ID Akun  : {username}".format(white = white, yellow = yellow, username = user['username']))
            print ("{white}[{yellow}!{white}] Status   : Gagal\n".format(white = white, yellow = yellow))
        except Exception as err:
          print ("{white}[{yellow}+{white}] Nama akun: {nama}".format(white = white, yellow = yellow, nama = user['name']), file = sys.stderr)
          print ("{white}[{yellow}+{white}] ID Akun  : {username}".format(white = white, yellow = yellow, username = user['username']), file = sys.stderr)
          print ("{white}[{red}!{white}] Status   : Error {white}({red}{err}{white}){reset}\n".format(white = white, red = red, err = err, reset = reset), file = sys.stderr)



  def add_friends_suges(self, limit = 5):
    print("{white}[{yellow}+{white}] Memulai bot Add Friends Sugestion{reset}".format(white = white, yellow = yellow, reset = reset))
    friends = BeautifulSoup(self.session.get(urljoin(self.host,'/friends/center/suggestions/')).content,'html.parser')
    saran = friends.findAll('img', alt = re.compile("(.*), profile picture"))

    if len(saran) <= 0:
      print("{white}[{red}!{white}] {yellow}Tidak ada saran pertemanan{reset}\n".format(white = white, red = red,yellow = yellow,reset = reset))
    else:
      print("")
      for akun in saran[0:limit]:
        try:
          profile = self.__get_profile_hovercard(akun)
          add_url = akun.find_next("a", href = re.compile("\/a\/friends\/add"))
          if add_url is None:
            print ("{white}[{red}+{white}] Nama akun: {nama}".format(white = white, red = red,nama = profile['name']))
            print ("{white}[{red}+{white}] ID Akun  : {fbid}".format(white = white, red = red, fbid = profile['username']))
            print ("{white}[{red}!{white}] Status   : Terjadi Kesalahan\n".format(white = white, red = red))
            continue

          req = self.session.get(urljoin(self.host,add_url['href']))

          if req.ok:
            print ("{white}[{green}+{white}] Nama akun: {nama}".format(white = white, green = green, nama = profile['name']))
            print ("{white}[{green}+{white}] ID Akun  : {username}".format(white = white, green = green, username = profile['username']))
            print ("{white}[{green}✓{white}] Status   : Sukses\n".format(white = white, green = green))
          else:
            print ("{white}[{yellow}+{white}] Nama akun: {nama}".format(white = white, yellow = yellow, nama = profile['name']))
            print ("{white}[{yellow}+{white}] ID Akun  : {username}".format(white = white, yellow = yellow, username = profile['username']))
            print ("{white}[{yellow}!{white}] Status   : Gagal\n".format(white = white, yellow = yellow))

        except Exception as err:
          print ("{white}[{yellow}+{white}] Nama akun: {nama}".format(white = white, yellow = yellow, nama = profile['name']), file = sys.stderr)
          print ("{white}[{yellow}+{white}] ID Akun  : {username}".format(white = white, yellow = yellow, username = profile['username']), file = sys.stderr)
          print ("{white}[{red}!{white}] Status   : Error {white}({red}{err}{white}){reset}\n".format(white = white, red = red, err = err, reset = reset), file = sys.stderr)

  def acc_friends(self, limit = 5):
    print("{white}[{yellow}+{white}] Memulai bot Auto Acc Friends{reset}".format(white = white, yellow = yellow, reset = reset))
    req = BeautifulSoup(self.session.get(urljoin(self.host,'/friends/center/requests')).content,'html.parser')
    acc = req.findAll('img', alt = re.compile('(.*), profile picture'))

    if len(acc) <= 0:
      print("{white}[{red}!{white}] {yellow}Tidak ada permintaan pertemanan{reset}".format(white = white, red = red, yellow = yellow, reset = reset))
    else:
      print("")
      for akun in acc[0:limit]:
        try:
          profile = self.__get_profile_hovercard(akun)
          acc_url = akun.find_next("a", href = re.compile("^\/a\/notifications\.php\?confirm"))

          if acc_url is None:
            print ("{white}[{red}+{white}] Nama akun: {nama}".format(white = white, red = red, nama = profile['name']))
            print ("{white}[{red}+{white}] ID Akun  : {username}".format(white = white, red = red, username = profile['username']))
            print ("{white}[{red}!{white}] Status   : Tidak dapat menerima permintaan\n".format(white = white, red = red))
            continue

          req = self.session.get(urljoin(self.host, acc_url['href']))

          if req.ok:
            print ("{white}[{green}+{white}] Nama akun: {nama}".format(white = white, green = green, nama = profile['name']))
            print ("{white}[{green}+{white}] ID Akun  : {username}".format(white = white, green = green, username = profile['username']))
            print ("{white}[{green}✓{white}] Status   : Sukses\n".format(white = white, green = green))
          else:
            print ("{white}[{yellow}+{white}] Nama akun: {nama}".format(white = white, yellow = yellow, nama = profile['name']))
            print ("{white}[{yellow}+{white}] ID Akun  : {username}".format(white = white, yellow = yellow, username = profile['username']))
            print ("{white}[{yellow}!{white}] Status   : Gagal\n".format(white = white, yellow = yellow))
        except Exception as err:
          print ("{white}[{yellow}+{white}] Nama akun: {nama}".format(white = white, yellow = yellow, nama = profile['name']), file = sys.stderr)
          print ("{white}[{yellow}+{white}] ID Akun  : {username}".format(white = white, yellow = yellow, username = profile['username']), file = sys.stderr)
          print ("{white}[{red}!{white}] Status   : Error {white}({red}{err}{white}){reset}\n".format(white = white, red = red, err = err, reset = reset), file = sys.stderr)

  def like_post_beranda(self, limit = 5):
    print("{white}[{yellow}+{white}] Memulai bot Like Post Beranda{reset}".format(white = white, yellow = yellow, reset = reset))
    postingan = self.__getPostBeranda(limit)

    if len(postingan) <= 0:
      print("{white}[{red}!{white}] {yellow}Tidak ada postingan pada beranda{reset}".format(white = white, red = red,yellow = yellow, reset = reset))
    else:
      print("")
      for post in postingan[0:limit]:
        author = post['author']
        caption = post['caption']
        action_like = post['action_like']
        upload_time = post['upload_time']

        if action_like is None:
          print("{white}[{yellow}!{white}] Author  : {cyan}{author}{reset}".format(white = white, yellow = yellow, cyan = cyan,author = author, reset = reset), file = sys.stderr)
          print("{white}[{yellow}!{white}] Caption : {cyan}{caption}{reset}".format(white = white, yellow = yellow, cyan = cyan, caption = caption, reset = reset), file = sys.stderr)
          print("{white}[{yellow}!{white}] Upload  : {cyan}{upload_time}{reset}".format(white = white, yellow = yellow, cyan = cyan, upload_time = upload_time, reset = reset), file = sys.stderr)
          print("{white}[{red}!{white}] Status  : {green}Tidak dapat memberikan like{reset}\n".format(white = white, red = red, green = green, reset = reset))
          continue
        try:
          if self.session.get(action_like).ok:
            print("{white}[{green}✓{white}] Author  : {cyan}{author}{reset}".format(white = white, green = green, cyan = cyan, author = author, reset = reset))
            print("{white}[{green}✓{white}] Caption : {cyan}{caption}{reset}".format(white = white, green = green, cyan = cyan, caption = caption,reset = reset))
            print("{white}[{green}✓{white}] Upload  : {cyan}{upload_time}{reset}".format(white = white, green = green, cyan = cyan, upload_time = upload_time, reset = reset))
            print("{white}[{green}✓{white}] Status  : {green}Sukses{reset}\n".format(white = white, green = green, reset = reset))
          else:
            print("{white}[{yellow}!{white}] Author  : {cyan}{author}{reset}".format(white = white, yellow = yellow, cyan = cyan, author = author, reset = reset), file = sys.stderr)
            print("{white}[{yellow}!{white}] Caption : {cyan}{caption}{reset}".format(white = white, yellow = yellow, cyan = cyan, caption = caption, reset = reset), file = sys.stderr)
            print("{white}[{yellow}!{white}] Upload  : {cyan}{upload_time}{reset}".format(white = white, yellow = yellow, cyan = cyan, upload_time = upload_time, reset = reset), file = sys.stderr)
            print("{white}[{yellow}!{white}] Status  : {red}Gagal{reset}\n".format(white = white, yellow = yellow, red = red, reset = reset), file = sys.stderr)
        except Exception as err:
          print("{white}[{yellow}!{white}] Author  : {cyan}{author}{reset}".format(white = white, yellow = yellow, cyan = cyan, author = author, reset = reset), file = sys.stderr)
          print("{white}[{yellow}!{white}] Caption : {cyan}{caption}{reset}".format(white = white, yellow = yellow, cyan = cyan, caption = caption, reset = reset), file = sys.stderr)
          print("{white}[{yellow}!{white}] Upload  : {cyan}{upload_time}{reset}".format(white = white, yellow = yellow, cyan = cyan, upload_time = upload_time, reset = reset), file = sys.stderr)
          print("{white}[{yellow}!{white}] Status  : {white}Error {white}({red}{err}{white}){reset}\n".format(white = white, yellow = yellow, red = red, err = err, reset = reset), file = sys.stderr)

  def comment_post_beranda(self,limit = 5):
    print("{white}[{yellow}+{white}] Memulai bot Comment Post Beranda{reset}".format(white = white, yellow = yellow, reset = reset))
    post = self.__getPostBeranda(limit)
    kata = ["Terima Kasih","Makasih","Good Job","Semoga Sukses"]

    if len(post) <= 0:
      print("{white}[{red}!{white}] {yellow}Tidak ada postingan pada beranda{reset}".format(white = white, red = red,yellow = yellow, reset = reset))
    else:
      print("")

      for moya in post[0:limit]:
        try:
          komen = random.choice(kata)
          if moya['post_url'] is None:
            print("{white}[{yellow}!{white}] Author  : {cyan}{author}{reset}".format(white = white, yellow = yellow, cyan = cyan,author = moya['author'], reset = reset), file = sys.stderr)
            print("{white}[{yellow}!{white}] Caption : {cyan}{caption}{reset}".format(white = white, yellow = yellow, cyan = cyan, caption = moya['caption'], reset = reset), file = sys.stderr)
            print("{white}[{yellow}!{white}] Upload  : {cyan}{upload_time}{reset}".format(white = white, yellow = yellow, cyan = cyan, upload_time = moya['upload_time'], reset = reset), file = sys.stderr)
            print("{white}[{yellow}!{white}] Comment : {cyan}{komen}{reset}".format(white = white, yellow = yellow, cyan = cyan, komen = komen, reset = reset), file = sys.stderr)
            print("{white}[{red}!{white}] Status  : {yellow}Terjadi kesalahan :({reset}\n".format(white = white, red = red, yellow = yellow, reset = reset))
            continue

          if self.post_parser(moya['post_url']).send_comment(komen):
            print("{white}[{green}✓{white}] Author  : {cyan}{author}{reset}".format(white = white, green = green, cyan = cyan, author = moya['author'], reset = reset))
            print("{white}[{green}✓{white}] Caption : {cyan}{caption}{reset}".format(white = white, green =	 green, cyan = cyan, caption = moya['caption'],reset = reset))
            print("{white}[{green}✓{white}] Upload  : {cyan}{upload_time}{reset}".format(white = white, green = green, cyan = cyan, upload_time = moya['upload_time'], reset = reset))
            print("{white}[{green}✓{white}] Comment : {cyan}{komen}{reset}".format(white = white, green = green, cyan = cyan, komen = komen, reset = reset))
            print("{white}[{green}✓{white}] Status  : {green}Sukses{reset}\n".format(white = white, green = green, reset = reset))
          else:
            print("{white}[{yellow}!{white}] Author  : {cyan}{author}{reset}".format(white = white, yellow = yellow, cyan = cyan, author = moya['author'], reset = reset), file = sys.stderr)
            print("{white}[{yellow}!{white}] Caption : {cyan}{caption}{reset}".format(white = white, yellow = yellow, cyan = cyan, caption = moya['caption'], reset = reset), file = sys.stderr)
            print("{white}[{yellow}!{white}] Upload  : {cyan}{upload_time}{reset}".format(white = white, yellow = yellow, cyan = cyan, upload_time = moya['upload_time'], reset = reset), file = sys.stderr)
            print("{white}[{yellow}!{white}] Comment : {cyan}{komen}{reset}".format(white = white, yellow = yellow, cyan = cyan, komen = komen, reset = reset), file = sys.stderr)
            print("{white}[{yellow}!{white}] Status  : {red}Gagal{reset}\n".format(white = white, yellow = yellow, red = red, reset = reset), file = sys.stderr)
        except Exception as err:
          print("{white}[{yellow}!{white}] Author  : {cyan}{author}{reset}".format(white = white, yellow = yellow, cyan = cyan, author = moya['author'], reset = reset), file = sys.stderr)
          print("{white}[{yellow}!{white}] Caption : {cyan}{caption}{reset}".format(white = white, yellow = yellow, cyan = cyan, caption = moya['caption'], reset = reset), file = sys.stderr)
          print("{white}[{yellow}!{white}] Upload  : {cyan}{upload_time}{reset}".format(white = white, yellow = yellow, cyan = cyan, upload_time = moya['upload_time'], reset = reset), file = sys.stderr)
          print("{white}[{yellow}!{white}] Comment : {cyan}{komen}{reset}".format(white = white, yellow = yellow, cyan = cyan, komen = komen, reset = reset), file = sys.stderr)
          print("{white}[{yellow}!{white}] Status  : {white}Error {white}({red}{err}{white}){reset}\n".format(white = white, yellow = yellow, red = red, err = err, reset = reset), file = sys.stderr)

  def gantiPassword(self):
    print ("{white}[{yellow}+{white}] Kamu Punya 3 Kesempatan Untuk Mengganti Password {white}[{yellow}+{white}]".format(white = white, yellow = yellow))

    for i in range(3):
      try:
        old_pw = input("{white}[{cyan}?{white}] Password Lama : ".format(white = white, cyan = cyan))
        new_pw = input("{white}[{cyan}?{white}] Password Baru : ".format(white = white, cyan = cyan))
        ganti = settings.ChangePassword(self, old_pw, new_pw)

        if ganti:
          print("{white}[{green}✓{white}] Berhasil mengganti password\n".format(white = white, green = green))
          break
        else:
          print ("{white}[{red}!{white}] {red}Gagal mengganti password\n".format(white = white, red = red))
      except Exception as err:
        print ("{white}[{red}!{white}] {red}{err}\n".format(white = white, red = red, err = err))

  def updateMail(self):
    while True:
      newMail = input(f"{white}[{red}?{white}] Masukkan Email Baru : ")
      if self.__addEmail(newMail): break

    self.__confirmEmail()
    self.__updatePrimaryMail(newMail)
    self.__deleteEmail()

  def shareToGroup(self, posturl, limit = 3):
    grup = self.__getGroups(limit)

    if len(grup) <= 0:
      print(f"{white}[{red}!{white}] {red}Akun facebook kamu tidak mempunyai grup!")
    else:
      posts = self.post_parser(posturl)
      posts.send_react('like')
      if posts.can_comment:
        posts.send_comment(random.choice(['Keren','Makasih','Mantap','Wow']))
        print (f"{white}[{green}✓{white}] {green}Berhasil memposting komentar ke post")
      else:
        print (f"{white}[{yellow}+{white}] {yellow}Tidak dapat memposting komentar ke post")

      posturl = (urlparse(posts.post_url)._replace(netloc = 'www')).geturl()
      for groups in grup:
        html = BeautifulSoup(self.session.get(groups['url']).content,'html.parser')
        form = html.find('form', action = re.compile('^\/composer\/mbasic'))
        if form is None:
          print (f"{white}[{red}!{white}] {red}Tidak dapat memposting ke grup {white}\"{yellow}{groups['name']}{white}\"")
          continue
        else:
          data = {i['name']:i['value'] for i in form.findAll('input', attrs = {'type':'hidden','name':True,'value':True})}
          data['xc_message'] = posturl
          data['view_post'] = form.find('input', attrs = {'name':'view_post'}).get('value')
          submit = self.session.post(urljoin(self.host,form['action']), data = data)
          if submit.ok:
            print (f"{white}[{green}✓{white}] {green}Berhasil membagikan post ke grup {groups['name']}")
          else:
            print (f"{white}[{red}!{white}] {red}Gagal membagikan post ke grup {groups['name']}")
