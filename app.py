import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# Sayfa ayarları
st.set_page_config(
    page_title="Belediye Hizmet Kalitesi Analiz",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Özel CSS stilleri
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# 1) SABİTLER VE YARDIMCI FONKSİYONLAR
# ----------------------------

HIZMET_ALANLARI = {
    "ulasim": "🚌 Ulaşım Hizmetleri",
    "temizlik": "🧹 Temizlik ve Çevre",
    "altyapi": "🔧 Altyapı Hizmetleri",
    "parklar": "🌳 Parklar ve Yeşil Alanlar",
    "iletisim": "📞 Belediye İletişimi"
}

HIZMET_KODLARI = ["ulasim", "temizlik", "altyapi", "parklar", "iletisim"]

OLUMLU_KELIMELER = [
    "iyi", "güzel", "memnun", "rahat", "kolay", "hızlı", "düzenli",
    "güvenli", "yakın", "hizmet", "başarılı", "uygun", "gelişmiş",
    "harika", "mükemmel", "tamam", "yeterli", "temiz", "düzgün",
    "verimli", "etkili", "iyileşti", "tamamlandı"
]

OLUMSUZ_KELIMELER = [
    "kötü", "yetersiz", "sorun", "eksik", "bozuk", "düzensiz", "geç",
    "kalitesiz", "uzak", "zor", "hantal", "gürültü", "çalışmıyor",
    "aksıyor", "yoğun", "sıkıntı", "stresli", "berbat", "feci",
    "iğrenç", "kara", "kirli", "eski", "harap", "perişan"
]

# ----------------------------
# 2) SENTETİK VERİ ÜRETME
# ----------------------------

def sentetik_veri_olustur():
    """150 vatandaşın sentetik anket verisini oluşturur."""
    np.random.seed(42)
    n = 150

    mahalleler = [
        "Merkez", "Bahçelievler", "İnönü", "Sakarya", "Yeşilova",
        "Güzeltepe", "Akarsu", "Yıldız", "Köyceğiz", "Yenimahalle"
    ]

    veri = {
        "vatandas_id": np.arange(1, n + 1),
        "yas": np.random.randint(18, 75, n),
        "mahalle": np.random.choice(mahalleler, n),
        "cinsiyet": np.random.choice(["Erkek", "Kadın", "Diğer"], n),
        "ulasim": np.random.randint(1, 6, n),
        "temizlik": np.random.randint(1, 6, n),
        "altyapi": np.random.randint(1, 6, n),
        "parklar": np.random.randint(1, 6, n),
        "iletisim": np.random.randint(1, 6, n),
    }

    df = pd.DataFrame(veri)

    # Yapay yorumlar oluştur
    yorumlar = []
    for i in range(n):
        puanlar = df.loc[i, HIZMET_KODLARI].to_dict()
        ortalama_puan = np.mean(list(puanlar.values()))
        en_dusuk_hizmet = min(puanlar, key=puanlar.get)

        # Genel yorum
        if ortalama_puan >= 4.2:
            temel = "Belediye hizmetlerinden genel olarak memnunum. "
        elif ortalama_puan >= 3.0:
            temel = "Hizmetler bazı alanlarda iyiyken, birkaç konuda iyileştirmeye ihtiyaç var. "
        else:
            temel = "Belediye hizmetleri bazı alanlarda oldukça yetersiz. "

        # Sorun alanı haritası
        sorun_haritasi = {
            "ulasim": "Ulaşım hizmetlerinde zaman zaman sorun yaşıyorum ve otobüslerin düzeni daha iyi olmalı. Sefer saatleri düzenlenmeli.",
            "temizlik": "Temizlik ve çevre düzeni konusunda daha özen gösterilmesini istiyorum. Sokaklarda daha sık temizlik yapılması gerekiyor.",
            "altyapi": "Altyapı çalışmaları daha hızlı ve düzenli yapılmalı. Su kesilmeleri ve elektrik sorunları sık yaşanıyor.",
            "parklar": "Parklar ve yeşil alanların bakımı daha iyi olmalı. Çocuk oyun alanları daha güvenli hale getirilmeli.",
            "iletisim": "Belediye iletişimi daha açık, hızlı ve erişilebilir olmalı. Şikayetlerin çözümü daha hızlı gerçekleşmeli."
        }

        yorum = temel + sorun_haritasi[en_dusuk_hizmet]
        yorumlar.append(yorum)

    df["yorum"] = yorumlar
    df["memnuniyet_puani"] = df[HIZMET_KODLARI].mean(axis=1)
    df["anket_tarihi"] = pd.Timestamp.now().date()

    return df

# ----------------------------
# 3) YORUM ANALİZİ
# ----------------------------

def yorumları_analiz_et(df):
    """Yorumların duygusunu analiz eder."""
    sonuc_df = df.copy()

    def duygu_puani_hesapla(yorum):
        kucuk_yorum = yorum.lower()
        olumlu_sayı = sum(1 for kelime in OLUMLU_KELIMELER if kelime in kucuk_yorum)
        olumsuz_sayı = sum(1 for kelime in OLUMSUZ_KELIMELER if kelime in kucuk_yorum)
        return olumlu_sayı - olumsuz_sayı

    def duygu_etiketi(puan):
        if puan > 0:
            return "Olumlu ✅"
        elif puan < 0:
            return "Olumsuz ❌"
        return "Nötr ⚪"

    sonuc_df["yorum_puani"] = sonuc_df["yorum"].apply(duygu_puani_hesapla)
    sonuc_df["yorum_duygusu"] = sonuc_df["yorum_puani"].apply(duygu_etiketi)

    return sonuc_df

# ----------------------------
# 4) İSTATİSTİKSEL ANALİZLER
# ----------------------------

def hizmet_ortalamalarını_hesapla(df):
    """Her hizmet alanının ortalamasını hesaplar."""
    ortalamaları = []
    for kod in HIZMET_KODLARI:
        ort = df[kod].mean()
        ortalamaları.append({
            "kod": kod,
            "hizmet_adı": HIZMET_ALANLARI[kod],
            "ortalama_puan": round(ort, 2),
            "vatandas_sayı": len(df)
        })
    
    return pd.DataFrame(ortalamaları).sort_values("ortalama_puan")

def oncelikli_alanları_belirle(ortalama_df):
    """Öncelik durumuna göre hizmet alanlarını sınıflandırır."""
    sonuc = ortalama_df.copy()
    
    def oncelik_belirle(puan):
        if puan < 2.5:
            return "🔴 ACİL"
        elif puan < 3.5:
            return "🟡 ÖNCELİKLİ"
        elif puan < 4.5:
            return "🟢 İYİ"
        else:
            return "🟢 MÜKEMMEL"
    
    sonuc["oncelik_durumu"] = sonuc["ortalama_puan"].apply(oncelik_belirle)
    return sonuc.sort_values("ortalama_puan")

def demografik_analiz(df):
    """Yaş ve cinsiyet bazında analiz."""
    yas_gurupları = []
    for grup_adı, (min_yas, max_yas) in [
        ("18-30", (18, 30)),
        ("31-45", (31, 45)),
        ("46-60", (46, 60)),
        ("61+", (61, 75))
    ]:
        alt_df = df[(df["yas"] >= min_yas) & (df["yas"] <= max_yas)]
        if len(alt_df) > 0:
            yas_gurupları.append({
                "yas_grubu": grup_adı,
                "memnuniyet_ort": round(alt_df["memnuniyet_puani"].mean(), 2),
                "kisi_sayı": len(alt_df)
            })
    
    return pd.DataFrame(yas_gurupları)

def mahalle_analizi(df):
    """Mahalle bazında memnuniyet analizi."""
    mahalle_data = []
    for mahalle in df["mahalle"].unique():
        alt_df = df[df["mahalle"] == mahalle]
        mahalle_data.append({
            "mahalle": mahalle,
            "memnuniyet_ort": round(alt_df["memnuniyet_puani"].mean(), 2),
            "kisi_sayı": len(alt_df)
        })
    
    return pd.DataFrame(mahalle_data).sort_values("memnuniyet_ort", ascending=False)

# ----------------------------
# 5) CSV DOĞRULAMA
# ----------------------------

def csv_dosyasını_doğrula(df):
    """Yüklenen CSV dosyasının gerekli sütunlara sahip olup olmadığını kontrol eder."""
    gerekli = ["ulasim", "temizlik", "altyapi", "parklar", "iletisim", "yorum"]
    eksik = [sütun for sütun in gerekli if sütun not in df.columns]
    
    if eksik:
        raise ValueError(
            f"CSV dosyasında eksik sütunlar var: {', '.join(eksik)}. "
            f"Gerekli sütunlar: {', '.join(gerekli)}"
        )

# ----------------------------
# 6) RAPOR OLUŞTURMA
# ----------------------------

def rapor_oluştur(df, ortalama_df, oncelik_df):
    """Detaylı analiz raporu metin formatında oluşturur."""
    rapor = f"""
╔════════════════════════════════════════════════════════════════╗
║        BELEDIYE HİZMET KALİTESİ ANALİZ RAPORU                 ║
║            {datetime.now().strftime('%d.%m.%Y %H:%M')}
╚════════════════════════════════════════════════════════════════╝

📊 GENEL İSTATİSTİKLER
{'='*60}
• Katılımcı Sayısı: {len(df)} vatandaş
• Genel Memnuniyet: {df['memnuniyet_puani'].mean():.2f}/5.00
• En Yüksek Memnuniyet: {ortalama_df['ortalama_puan'].max():.2f}
• En Düşük Memnuniyet: {ortalama_df['ortalama_puan'].min():.2f}

📈 HİZMET ALANLARI ANALİZİ
{'='*60}
"""
    
    for _, satır in ortalama_df.iterrows():
        rapor += f"\n{satır['hizmet_adı']}\n"
        rapor += f"  Ortalama Puan: {satır['ortalama_puan']:.2f}/5.00\n"
        rapor += f"  Durumu: {oncelik_df[oncelik_df['kod'] == satır['kod']]['oncelik_durumu'].values[0]}\n"
    
    rapor += f"\n\n🎯 ÖNCELİKLİ İYİLEŞTİRME ALANLARI\n{'='*60}\n"
    
    acil = oncelik_df[oncelik_df['oncelik_durumu'].str.contains('ACİL')]
    oncelikli = oncelik_df[oncelik_df['oncelik_durumu'].str.contains('ÖNCELİKLİ')]
    
    if len(acil) > 0:
        rapor += "\n🔴 ACİL MÜDAHALE GEREKENLERİ:\n"
        for _, satır in acil.iterrows():
            rapor += f"  • {satır['hizmet_adı']} ({satır['ortalama_puan']:.2f})\n"
    
    if len(oncelikli) > 0:
        rapor += "\n🟡 ÖNCELİKLE ÇÖZÜLMESİ GEREKEN:\n"
        for _, satır in oncelikli.iterrows():
            rapor += f"  • {satır['hizmet_adı']} ({satır['ortalama_puan']:.2f})\n"
    
    rapor += f"\n\n💬 YORUM DUYGU ANALİZİ\n{'='*60}\n"
    duygu_sayıları = df['yorum_duygusu'].value_counts()
    for duygu, sayı in duygu_sayıları.items():
        yüzde = (sayı / len(df) * 100)
        rapor += f"  {duygu}: {sayı} ({yüzde:.1f}%)\n"
    
    return rapor

# ----------------------------
# 7) ANA UYGULAMA
# ----------------------------

st.title("🏙️ Akıllı Belediye Hizmet Kalitesi Analiz Sistemi")
st.caption("📚 Kamu yönetimi öğrencileri için eğitim amaçlı, yapay zeka destekli yorum analizi ve interaktif görselleştirme uygulaması")

# SIDEBAR
st.sidebar.header("⚙️ Ayarlar")
st.sidebar.write("Veri kaynağını seçin:")

seçenek = st.sidebar.radio(
    "Veri kaynağı:",
    ("📊 Sentetik Veriler Kullan", "📁 CSV Dosyası Yükle"),
    label_visibility="collapsed"
)

# Veri yükleme
if seçenek == "📁 CSV Dosyası Yükle":
    uploaded_file = st.sidebar.file_uploader(
        "CSV dosyası seçin",
        type=["csv"],
        help="Gerekli sütunlar: ulasim, temizlik, altyapi, parklar, iletisim, yorum"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            csv_dosyasını_doğrula(df)
            st.sidebar.success("✅ CSV dosyası başarıyla yüklendi!")
        except Exception as e:
            st.error(f"❌ CSV yüklenirken hata oluştu:\n{e}")
            st.stop()
    else:
        st.info("📥 Lütfen bir CSV dosyası yükleyiniz.")
        st.stop()
else:
    df = sentetik_veri_olustur()

# Veriyi analiz et
df = yorumları_analiz_et(df)
ortalama_df = hizmet_ortalamalarını_hesapla(df)
oncelik_df = oncelikli_alanları_belirle(ortalama_df)
yas_analiz = demografik_analiz(df)
mahalle_analiz = mahalle_analizi(df)

# GENEL METRİKLER
st.subheader("📊 Temel Metrikler")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Toplam Katılımcı", f"{len(df)} kişi")

with col2:
    genel_ort = df['memnuniyet_puani'].mean()
    st.metric("Genel Memnuniyet", f"{genel_ort:.2f}/5.00")

with col3:
    olumlu_sayı = len(df[df['yorum_duygusu'] == 'Olumlu ✅'])
    st.metric("Olumlu Yorumlar", f"{olumlu_sayı} ({olumlu_sayı/len(df)*100:.1f}%)")

with col4:
    olumsuz_sayı = len(df[df['yorum_duygusu'] == 'Olumsuz ❌'])
    st.metric("Olumsuz Yorumlar", f"{olumsuz_sayı} ({olumsuz_sayı/len(df)*100:.1f}%)")

st.divider()

# TAB 1: VERİ VE ANALİZ
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Anket Verisi",
    "📊 Hizmet Analizi",
    "💬 Yorum Analizi",
    "👥 Demografik",
    "📥 İndir"
])

# TAB 1: ANKET VERİSİ
with tab1:
    st.subheader("Vatandaş Anket Verileri")
    st.write(f"Toplam {len(df)} vatandaşın cevapları aşağıda görülmektedir:")
    
    col1, col2 = st.columns(2)
    with col1:
        filtere_mahalle = st.multiselect(
            "Mahalle seç:",
            df['mahalle'].unique(),
            default=df['mahalle'].unique()
        )
    
    with col2:
        min_yas, max_yas = st.slider("Yaş aralığı:", 18, 75, (18, 75))
    
    # Filtreleme
    filtered_df = df[
        (df['mahalle'].isin(filtere_mahalle)) &
        (df['yas'] >= min_yas) &
        (df['yas'] <= max_yas)
    ]
    
    # Göster
    st.dataframe(
        filtered_df[[
            'vatandas_id', 'yas', 'cinsiyet', 'mahalle',
            'ulasim', 'temizlik', 'altyapi', 'parklar', 'iletisim',
            'memnuniyet_puani'
        ]].reset_index(drop=True),
        use_container_width=True,
        height=400
    )
    
    st.write(f"Gösterilen kayıt: {len(filtered_df)} / {len(df)}")

# TAB 2: HİZMET ANALİZİ
with tab2:
    st.subheader("Hizmet Alanlarına Göre Ortalama Puanlar")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Grafik 1: Bar Grafik
        fig_bar = px.bar(
            ortalama_df,
            x='ortalama_puan',
            y='hizmet_adı',
            orientation='h',
            color='ortalama_puan',
            color_continuous_scale='RdYlGn',
            range_x=[0, 5],
            title='Hizmet Alanları Ortalama Puanları',
            labels={'ortalama_puan': 'Ortalama Puan (1-5)', 'hizmet_adı': 'Hizmet Alanı'},
            text='ortalama_puan'
        )
        fig_bar.update_traces(textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.subheader("Öncelik Durumu")
        for _, satır in oncelik_df.iterrows():
            st.write(f"{satır['hizmet_adı']}")
            st.write(f"**{satır['oncelik_durumu']}**")
            st.write(f"Puan: {satır['ortalama_puan']:.2f}")
            st.divider()
    
    # Memnuniyet Dağılımı
    st.subheader("Memnuniyet Seviyeleri Dağılımı")
    
    df['memnuniyet_seviyesi'] = pd.cut(
        df['memnuniyet_puani'],
        bins=[0, 2.5, 3.5, 4.5, 5],
        labels=['Düşük (0-2.5)', 'Orta (2.5-3.5)', 'İyi (3.5-4.5)', 'Çok İyi (4.5-5)']
    )
    
    seviye_sayısı = df['memnuniyet_seviyesi'].value_counts().sort_index()
    
    fig_pie = px.pie(
        values=seviye_sayısı.values,
        names=seviye_sayısı.index,
        title='Memnuniyet Seviyeleri Oranı',
        color_discrete_sequence=['#ff4444', '#ffaa44', '#aadd44', '#44dd44']
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Hizmet Karşılaştırması
    st.subheader("Hizmet Alanları Kutu Grafiği")
    
    kutu_verisi = []
    for kod in HIZMET_KODLARI:
        kutu_verisi.extend([
            {'Hizmet': HIZMET_ALANLARI[kod], 'Puan': puan}
            for puan in df[kod].values
        ])
    
    kutu_df = pd.DataFrame(kutu_verisi)
    
    fig_box = px.box(
        kutu_df,
        x='Hizmet',
        y='Puan',
        title='Hizmet Alanlarında Puan Dağılımı',
        range_y=[0, 5]
    )
    st.plotly_chart(fig_box, use_container_width=True)

# TAB 3: YORUM ANALİZİ
with tab3:
    st.subheader("Açık Uçlu Yorum Analizi")
    
    col1, col2 = st.columns(2)
    
    # Yorum duygu dağılımı
    with col1:
        duygu_sayısı = df['yorum_duygusu'].value_counts()
        
        fig_duygu = px.bar(
            x=duygu_sayısı.index,
            y=duygu_sayısı.values,
            title='Yorumların Duygu Dağılımı',
            labels={'x': 'Duygu', 'y': 'Yorum Sayısı'},
            color=duygu_sayısı.index,
            color_discrete_map={
                'Olumlu ✅': '#44dd44',
                'Olumsuz ❌': '#ff4444',
                'Nötr ⚪': '#cccccc'
            }
        )
        st.plotly_chart(fig_duygu, use_container_width=True)
    
    # Yorum puanı dağılımı
    with col2:
        fig_puan = px.histogram(
            df,
            x='yorum_puani',
            nbins=20,
            title='Yorum Puanı Dağılımı',
            labels={'yorum_puani': 'Yorum Puanı', 'count': 'Frekans'},
            color_discrete_sequence=['#4488dd']
        )
        st.plotly_chart(fig_puan, use_container_width=True)
    
    st.divider()
    
    # Örnek yorumlar
    st.subheader("Örnek Yorumlar")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**🟢 Olumlu Yorumlar**")
        olumlu_df = df[df['yorum_duygusu'] == 'Olumlu ✅']
        if len(olumlu_df) > 0:
            for _, satır in olumlu_df.head(2).iterrows():
                st.info(f"ID {satır['vatandas_id']}: {satır['yorum'][:150]}...")
    
    with col2:
        st.write("**🟡 Nötr Yorumlar**")
        notr_df = df[df['yorum_duygusu'] == 'Nötr ⚪']
        if len(notr_df) > 0:
            for _, satır in notr_df.head(2).iterrows():
                st.warning(f"ID {satır['vatandas_id']}: {satır['yorum'][:150]}...")
    
    with col3:
        st.write("**🔴 Olumsuz Yorumlar**")
        olumsuz_df = df[df['yorum_duygusu'] == 'Olumsuz ❌']
        if len(olumsuz_df) > 0:
            for _, satır in olumsuz_df.head(2).iterrows():
                st.error(f"ID {satır['vatandas_id']}: {satır['yorum'][:150]}...")

# TAB 4: DEMOGRAFİK ANALİZ
with tab4:
    st.subheader("Demografik Analiz")
    
    col1, col2 = st.columns(2)
    
    # Yaş Grubu Analizi
    with col1:
        st.write("**Yaş Grubuna Göre Memnuniyet**")
        
        fig_yas = px.bar(
            yas_analiz,
            x='yas_grubu',
            y='memnuniyet_ort',
            title='Yaş Grubuna Göre Ortalama Memnuniyet',
            labels={'yas_grubu': 'Yaş Grubu', 'memnuniyet_ort': 'Memnuniyet Puanı'},
            range_y=[0, 5],
            color_discrete_sequence=['#4488dd']
        )
        fig_yas.add_hline(y=df['memnuniyet_puani'].mean(), line_dash="dash", 
                         line_color="red", annotation_text="Genel Ortalama")
        st.plotly_chart(fig_yas, use_container_width=True)
    
    # Mahalle Analizi
    with col2:
        st.write("**Mahalle Bazında Memnuniyet**")
        
        fig_mahalle = px.bar(
            mahalle_analiz.sort_values('memnuniyet_ort', ascending=True),
            y='mahalle',
            x='memnuniyet_ort',
            orientation='h',
            title='Mahalle Bazında Ortalama Memnuniyet',
            labels={'mahalle': 'Mahalle', 'memnuniyet_ort': 'Memnuniyet Puanı'},
            range_x=[0, 5],
            color_discrete_sequence=['#44aa44']
        )
        st.plotly_chart(fig_mahalle, use_container_width=True)
    
    # Cinsiyet Analizi
    col3, col4 = st.columns(2)
    
    with col3:
        st.write("**Cinsiyet Dağılımı**")
        cinsiyet_sayı = df['cinsiyet'].value_counts()
        fig_cinsiyet_pie = px.pie(
            values=cinsiyet_sayı.values,
            names=cinsiyet_sayı.index,
            title='Katılımcı Cinsiyetlerine Göre Dağılım'
        )
        st.plotly_chart(fig_cinsiyet_pie, use_container_width=True)
    
    with col4:
        st.write("**Cinsiyete Göre Memnuniyet**")
        cinsiyet_analiz = df.groupby('cinsiyet')['memnuniyet_puani'].mean().reset_index()
        fig_cinsiyet_bar = px.bar(
            cinsiyet_analiz,
            x='cinsiyet',
            y='memnuniyet_puani',
            title='Cinsiyete Göre Ortalama Memnuniyet',
            labels={'cinsiyet': 'Cinsiyet', 'memnuniyet_puani': 'Memnuniyet Puanı'},
            range_y=[0, 5],
            color_discrete_sequence=['#dd8844']
        )
        st.plotly_chart(fig_cinsiyet_bar, use_container_width=True)
    
    # Detaylı İstatistikler
    st.subheader("İstatistiksel Özet")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Yaş İstatistikleri**")
        st.table(pd.DataFrame({
            'Metrik': ['Minimum', 'Maksimum', 'Ortalama', 'Medyan'],
            'Değer': [
                f"{df['yas'].min()} yaş",
                f"{df['yas'].max()} yaş",
                f"{df['yas'].mean():.1f} yaş",
                f"{df['yas'].median():.0f} yaş"
            ]
        }))
    
    with col2:
        st.write("**Memnuniyet İstatistikleri**")
        st.table(pd.DataFrame({
            'Metrik': ['Minimum', 'Maksimum', 'Ortalama', 'Standart Sapma'],
            'Değer': [
                f"{df['memnuniyet_puani'].min():.2f}",
                f"{df['memnuniyet_puani'].max():.2f}",
                f"{df['memnuniyet_puani'].mean():.2f}",
                f"{df['memnuniyet_puani'].std():.2f}"
            ]
        }))

# TAB 5: İNDİR
with tab5:
    st.subheader("Rapor ve Veri İndirme")
    
    st.write("Aşağıdaki dosyaları indirebilirsiniz:")
    
    col1, col2, col3 = st.columns(3)
    
    # 1. Öncelik Raporu (CSV)
    with col1:
        st.subheader("1️⃣ Öncelik Raporu")
        rapor_df = oncelik_df[['hizmet_adı', 'ortalama_puan', 'oncelik_durumu']].copy()
        rapor_df.columns = ['Hizmet Alanı', 'Ortalama Puan', 'Öncelik Durumu']
        
        csv_data = rapor_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSV İndir",
            data=csv_data,
            file_name="belediye_oncelik_raporu.csv",
            mime="text/csv",
            key="oncelik_csv"
        )
    
    # 2. Tam Anket Verisi (CSV)
    with col2:
        st.subheader("2️⃣ Tam Anket Verisi")
        
        csv_veri = df[[
            'vatandas_id', 'yas', 'cinsiyet', 'mahalle',
            'ulasim', 'temizlik', 'altyapi', 'parklar', 'iletisim',
            'memnuniyet_puani', 'yorum_duygusu'
        ]].to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            label="📥 CSV İndir",
            data=csv_veri,
            file_name="belediye_anket_verisi.csv",
            mime="text/csv",
            key="veri_csv"
        )
    
    # 3. Detaylı Metin Raporu
    with col3:
        st.subheader("3️⃣ Detaylı Rapor")
        
        rapor_metni = rapor_oluştur(df, ortalama_df, oncelik_df)
        
        st.download_button(
            label="📥 TXT İndir",
            data=rapor_metni,
            file_name="belediye_detayli_raporu.txt",
            mime="text/plain",
            key="rapor_txt"
        )
    
    st.divider()
    
    # Rapor Önizlemesi
    st.subheader("Rapor Önizlemesi")
    st.text(rapor_oluştur(df, ortalama_df, oncelik_df))

# ALT KIŞIM
st.divider()
st.markdown("""
---
### 📚 Bu Uygulama Hakkında
- **Geliştirme Dili**: Python 3.9+
- **Web Framework**: Streamlit
- **Veri İşleme**: Pandas, NumPy
- **Görselleştirme**: Plotly
- **Barındırma**: Streamlit Community Cloud

### 🎓 Eğitim Amaçları
1. Kamu hizmetlerinin kalitesini ölçme
2. Vatandaş memnuniyeti analizini öğrenme
3. Veri analizi ve görselleştirme becerilerini geliştirme
4. Belediye yönetiminin karar alma sürecini anlama

### 👨‍💻 Teknik Özellikler
- Yapay zeka destekli yorum analizi
- İnteraktif Plotly grafikleri
- Türkçe tam dil desteği
- CSV yükle/indir özelliği
- Demografik analiz raporlaması

*Geliştirildi: 2024 | Kamu Yönetimi Eğitim Uygulaması*
""")
