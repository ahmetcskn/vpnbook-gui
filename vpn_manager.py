import requests
import zipfile
import io
import os
import subprocess
import time

class VPNBookManager:
    def __init__(self):
        self.base_url = "https://www.vpnbook.com"
        self.username = "vpnbook"
        self.current_password = None
        self.tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        self.openvpn_path = r'C:\Program Files\OpenVPN\bin\openvpn.exe'
        
    def download_config_files(self):
        """VPN yapılandırma dosyalarını indir"""
        try:
            # Eğer vpn_configs klasörü yoksa oluştur
            if not os.path.exists("vpn_configs"):
                print("vpn_configs klasörü oluşturuluyor...")
                os.makedirs("vpn_configs")
                
            # ZIP dosyasını indir
            zip_url = f"{self.base_url}/free-openvpn-account/vpnbook-openvpn-de20.zip"
            print(f"ZIP dosyası indiriliyor: {zip_url}")
            response = requests.get(zip_url)
            
            if response.status_code != 200:
                print(f"ZIP indirme hatası! Status code: {response.status_code}")
                return False
            
            # ZIP içeriğini çıkar
            print("ZIP dosyası açılıyor...")
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                # ZIP içeriğini göster
                print("ZIP içeriği:", zip_ref.namelist())
                zip_ref.extractall("vpn_configs")
                
            # İndirilen dosyaları listele
            config_files = [f for f in os.listdir("vpn_configs") if f.endswith('.ovpn')]
            print(f"İndirilen yapılandırma dosyaları: {config_files}")
            
            if not config_files:
                print("Hiç .ovpn dosyası bulunamadı!")
                return False
                
            return True
        except Exception as e:
            print(f"Yapılandırma dosyaları indirilirken hata: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_password(self):
        """Websitesinden güncel şifreyi al"""
        try:
            print("VPNBook şifresi alınıyor...")
            password_url = f"{self.base_url}/password.php"
            response = requests.get(password_url)
            
            # Resmi kaydet
            with open("temp_pwd.png", "wb") as f:
                f.write(response.content)
            
            # Tesseract ile OCR işlemi - özel konfigürasyon ile
            cmd = [
                self.tesseract_path,
                'temp_pwd.png',
                'stdout',
                '--psm', '6',  # Tek satır metin modu
                '--oem', '3',  # LSTM OCR Engine
                '-c', 'tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'  # Sadece alfanümerik karakterlere izin ver
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            
            # Geçici dosyayı sil
            os.remove("temp_pwd.png")
            
            if error:
                print(f"OCR hatası: {error.decode()}")
                return None
                
            password = output.decode().strip()
            print(f"Şifre başarıyla alındı: {password}")
            
            # Şifrenin doğru formatta olduğunu kontrol et
            if not password or len(password) < 4:  # VPNBook şifreleri genelde 4+ karakter
                print("Okunan şifre çok kısa veya boş!")
                return None
                
            self.current_password = password
            return password
            
        except Exception as e:
            print(f"Şifre alınırken hata: {e}")
            return None

    def connect_vpn(self, config_file):
        """OpenVPN bağlantısını başlat"""
        if not self.current_password:
            print("Şifre alınıyor...")
            self.get_password()
            
        try:
            print(f"VPN bağlantısı başlatılıyor... Seçilen config: {config_file}")
            
            # Dosyanın varlığını kontrol et
            if not os.path.exists(config_file):
                print(f"HATA: Config dosyası bulunamadı: {config_file}")
                return None
                
            # OpenVPN'in varlığını kontrol et
            if not os.path.exists(self.openvpn_path):
                print(f"HATA: OpenVPN bulunamadı: {self.openvpn_path}")
                return None
            
            # Kullanıcı adı ve şifre dosyası oluştur
            auth_file = os.path.join(os.getcwd(), "vpn_auth.txt")
            print(f"Kimlik dosyası oluşturuluyor: {auth_file}")
            with open(auth_file, "w") as f:
                f.write(f"{self.username}\n{self.current_password}")
            
            # Dosyanın oluşturulduğunu kontrol et
            if not os.path.exists(auth_file):
                print("HATA: Kimlik dosyası oluşturulamadı!")
                return None
            
            # OpenVPN komutunu hazırla
            cmd = [
                self.openvpn_path,
                "--config", os.path.abspath(config_file),
                "--auth-user-pass", auth_file,
                "--verb", "4",
                "--connect-retry", "1",  # Bağlantı denemesi sayısı
                "--connect-timeout", "10"  # Bağlantı zaman aşımı (saniye)
            ]
            
            print(f"Çalıştırılan komut: {' '.join(cmd)}")
            
            # OpenVPN'i başlat
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
                universal_newlines=True  # Metin modunda çıktı al
            )
            
            # Biraz bekle ve ilk çıktıları kontrol et
            time.sleep(1)
            
            # İlk çıktıları kontrol et
            print("\nOpenVPN başlatılıyor...")
            for _ in range(10):  # Daha fazla çıktı göster
                if process.poll() is not None:  # Süreç sonlandıysa
                    print("OpenVPN beklenmedik şekilde sonlandı!")
                    break
                    
                output = process.stdout.readline().strip()
                error = process.stderr.readline().strip()
                
                if output:
                    print(f"OpenVPN: {output}")
                if error:
                    print(f"OpenVPN Hata: {error}")
                    
                # Önemli hata mesajlarını kontrol et
                if any(msg in (output + error) for msg in [
                    "AUTH_FAILED", "TLS Error", "Connection refused",
                    "Cannot resolve host", "Network is unreachable"
                ]):
                    print("Kritik hata tespit edildi!")
                    process.terminate()
                    break
            
            # Şimdi kimlik dosyasını sil
            try:
                os.remove(auth_file)
                print("Kimlik dosyası silindi")
            except Exception as e:
                print(f"Kimlik dosyası silinirken hata: {e}")
            
            return process
            
        except Exception as e:
            print(f"VPN bağlantısı başlatılırken hata: {e}")
            import traceback
            traceback.print_exc()
            if 'auth_file' in locals() and os.path.exists(auth_file):
                try:
                    os.remove(auth_file)
                    print("Kimlik dosyası silindi (hata durumunda)")
                except:
                    pass
            return None 