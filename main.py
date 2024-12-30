from vpn_manager import VPNBookManager
import tkinter as tk
from tkinter import ttk, messagebox
import os

class VPNBookGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VPNBook Manager")
        self.vpn_manager = VPNBookManager()
        self.vpn_config_path = None  # VPN config dosyalarının yolu
        self.vpn_process = None
        self.connection_active = False
        
        # Pencere boyutunu ayarla
        self.root.geometry("400x300")
        self.setup_ui()
        
        # Başlangıçta mevcut dosyaları kontrol et
        self.download_configs()
        
    def setup_ui(self):
        # Ana çerçeve
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Yapılandırma dosyaları butonu
        ttk.Button(
            main_frame, 
            text="Yapılandırma Dosyalarını İndir",
            command=self.download_configs,
            width=30
        ).pack(pady=10)
        
        # Sunucu seçimi
        ttk.Label(main_frame, text="Sunucu Seçin:").pack(pady=5)
        self.server_var = tk.StringVar()
        self.server_combo = ttk.Combobox(
            main_frame,
            textvariable=self.server_var,
            width=30,
            state='readonly'
        )
        self.server_combo.pack(pady=5)
        
        # Combobox seçim olayını bağla
        self.server_combo.bind('<<ComboboxSelected>>', self.on_server_select)
        
        # Bağlan/Bağlantıyı Kes butonu
        self.connect_btn = ttk.Button(
            main_frame,
            text="Bağlan",
            command=self.toggle_connection,
            width=30
        )
        self.connect_btn.pack(pady=10)
        
        # Durum etiketi
        self.status_label = ttk.Label(
            main_frame, 
            text="Durum: Bağlantı yok",
            wraplength=350  # Uzun mesajları birden fazla satıra böl
        )
        self.status_label.pack(pady=10)
        
        # Başlangıçta sunucu listesini güncelle
        self.update_server_list()
        
    def download_configs(self):
        """Yapılandırma dosyalarını kontrol et veya indir"""
        self.status_label.config(text="Durum: Yapılandırma dosyaları kontrol ediliyor...")
        self.root.update()
        
        # Alt klasörü de kontrol et
        vpn_path = os.path.join("vpn_configs", "vpnbook-openvpn-de20")
        
        if os.path.exists(vpn_path):
            print(f"VPN klasörü bulundu: {vpn_path}")
            configs = []
            
            # Hem .ovpn hem de .OVPN uzantılı dosyaları kontrol et
            for file in os.listdir(vpn_path):
                if file.lower().endswith('.ovpn'):
                    configs.append(file)
                    
            if configs:
                print(f"Mevcut yapılandırma dosyaları: {configs}")
                self.status_label.config(text="Durum: Mevcut yapılandırma dosyaları kullanılıyor")
                self.server_combo['values'] = configs
                self.server_combo.set(configs[0])
                self.connect_btn['state'] = 'normal'
                
                # Alt klasör yolunu sakla
                self.vpn_config_path = vpn_path
                return True
                
            print("Klasörde .ovpn dosyası bulunamadı")
        
        # Mevcut dosya yoksa yeni indir
        return self._download_new_configs()

    def _download_new_configs(self):
        """Yeni yapılandırma dosyalarını indir"""
        if self.vpn_manager.download_config_files():
            configs = [f for f in os.listdir("vpn_configs") if f.lower().endswith('.ovpn')]
            if configs:
                self.status_label.config(text="Durum: Yapılandırma dosyaları indirildi")
                self.server_combo['values'] = configs
                self.server_combo.set(configs[0])
                self.connect_btn['state'] = 'normal'
                return True
        
        self.status_label.config(text="Durum: İndirme başarısız!")
        messagebox.showerror("Hata", "Yapılandırma dosyaları indirilemedi!")
        return False

    def update_server_list(self):
        """Sunucu listesini güncelle"""
        try:
            print("\nSunucu listesi güncelleniyor...")
            
            # Çalışma dizinini kontrol et
            current_dir = os.getcwd()
            print(f"Çalışma dizini: {current_dir}")
            
            # vpn_configs klasörünün tam yolunu al
            vpn_configs_path = os.path.join(current_dir, "vpn_configs")
            print(f"VPN configs dizini: {vpn_configs_path}")
            
            # Klasör kontrolü
            if not os.path.exists(vpn_configs_path):
                print(f"vpn_configs klasörü bulunamadı: {vpn_configs_path}")
                self.connect_btn['state'] = 'disabled'
                return
            
            # Klasör içeriğini listele
            all_files = os.listdir(vpn_configs_path)
            print(f"Klasördeki tüm dosyalar: {all_files}")
            
            # .ovpn dosyalarını filtrele
            configs = [f for f in all_files if f.endswith('.ovpn')]
            print(f"Bulunan .ovpn dosyaları: {configs}")
            
            if not configs:
                print("Hiç .ovpn dosyası bulunamadı!")
                self.connect_btn['state'] = 'disabled'
                return
                
            # Combobox'ı güncelle
            self.server_combo['values'] = configs
            self.server_combo.set(configs[0])
            self.connect_btn['state'] = 'normal'
            
            print(f"Combobox değerleri: {self.server_combo['values']}")
            print(f"Seçili değer: {self.server_var.get()}")
            
        except Exception as e:
            print(f"HATA: {str(e)}")
            import traceback
            traceback.print_exc()  # Detaylı hata mesajı
            self.connect_btn['state'] = 'disabled'

    def toggle_connection(self):
        """VPN bağlantısını aç/kapa"""
        if self.connect_btn['text'] == "Bağlan":
            config_file = self.server_var.get()
            if not config_file:
                messagebox.showwarning("Uyarı", "Lütfen bir sunucu seçin!")
                return
                
            # Tam dosya yolunu oluştur
            config_path = os.path.join(self.vpn_config_path, config_file)
            
            self.status_label.config(text="Durum: VPN bağlantısı kuruluyor...")
            self.root.update()
            
            process = self.vpn_manager.connect_vpn(config_path)
            if process:
                # Bağlantı durumunu kontrol etmek için yeni bir thread başlat
                import threading
                self.vpn_process = process
                self.connection_active = True
                threading.Thread(target=self.monitor_connection, daemon=True).start()
                
                self.status_label.config(text=f"Durum: {config_file} sunucusuna bağlanılıyor...")
                self.connect_btn['text'] = "Bağlantıyı Kes"
            else:
                self.status_label.config(text="Durum: Bağlantı başarısız!")
                messagebox.showerror("Hata", "VPN bağlantısı kurulamadı!")
        else:
            # Bağlantıyı kes
            if hasattr(self, 'vpn_process'):
                self.connection_active = False
                self.vpn_process.terminate()
                self.vpn_process = None
                
            self.connect_btn['text'] = "Bağlan"
            self.status_label.config(text="Durum: Bağlantı kesildi")

    def monitor_connection(self):
        """VPN bağlantı durumunu izle"""
        while self.connection_active and self.vpn_process:
            try:
                # Çıktıyı oku (farklı kodlamalar deneyerek)
                try:
                    output = self.vpn_process.stdout.readline().decode('utf-8', errors='ignore').strip()
                    error = self.vpn_process.stderr.readline().decode('utf-8', errors='ignore').strip()
                except UnicodeDecodeError:
                    try:
                        output = self.vpn_process.stdout.readline().decode('cp1252', errors='ignore').strip()
                        error = self.vpn_process.stderr.readline().decode('cp1252', errors='ignore').strip()
                    except:
                        output = ''
                        error = ''
                
                if output:
                    print(f"OpenVPN: {output}")
                if error:
                    print(f"OpenVPN Error: {error}")
                    
                # Başarılı bağlantı mesajlarını kontrol et
                if "Initialization Sequence Completed" in output:
                    self.status_label.config(text="Durum: VPN bağlantısı kuruldu")
                elif "AUTH_FAILED" in output:
                    self.status_label.config(text="Durum: Kimlik doğrulama başarısız!")
                    self.connect_btn['text'] = "Bağlan"
                    self.connection_active = False
                elif any(msg in output for msg in ["Connection reset", "Connection refused", "TLS Error", "TLS handshake failed"]):
                    print("Bağlantı hatası tespit edildi")
                    self.status_label.config(text="Durum: Bağlantı hatası!")
                    self.connect_btn['text'] = "Bağlan"
                    self.connection_active = False
                    
                # Süreç hala çalışıyor mu kontrol et
                if self.vpn_process.poll() is not None:
                    print("VPN bağlantısı sonlandı")
                    self.connection_active = False
                    self.status_label.config(text="Durum: Bağlantı kesildi")
                    self.connect_btn['text'] = "Bağlan"
                    break
                    
            except Exception as e:
                print(f"Bağlantı izleme hatası: {e}")
                import traceback
                traceback.print_exc()
                break

    def on_server_select(self, event):
        """Sunucu seçildiğinde çağrılır"""
        selected = self.server_var.get()
        print(f"Seçilen sunucu: {selected}")  # Debug için
        if selected:
            self.connect_btn['state'] = 'normal'
        else:
            self.connect_btn['state'] = 'disabled'

if __name__ == "__main__":
    app = VPNBookGUI()
    app.root.mainloop() 