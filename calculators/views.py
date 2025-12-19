from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count
from .models import Category, Thread, Answer, AnswerVote, Report
import base64
import hmac
import hashlib
import json
import random
import time

def _b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()

def _generate_token(user_id, username, exp_seconds=3600):
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({"sub": user_id, "username": username, "exp": int(time.time()) + exp_seconds}).encode())
    signing_input = f"{header}.{payload}".encode()
    signature = _b64url(hmac.new(settings.SECRET_KEY.encode(), signing_input, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"

def _verify_token(token):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected_sig = _b64url(hmac.new(settings.SECRET_KEY.encode(), signing_input, hashlib.sha256).digest())
        if not hmac.compare_digest(signature_b64, expected_sig):
            return None
        payload_json = base64.urlsafe_b64decode(payload_b64 + '==')
        payload = json.loads(payload_json.decode())
        if payload.get('exp', 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None

def chat_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '').lower()
            
            # Simulate AI delay for realism
            time.sleep(1)

            # Basic keyword-based response logic (Simulating AI)
            response = ""
            context_tool = (data.get('context_tool', '') or '').lower()
            intent = (data.get('intent', '') or '').lower()
            if intent == 'explain' and context_tool:
                if 'molekül' in context_tool:
                    response = "Molekül Ağırlığı hesaplayıcısı, formüldeki her elementin atom ağırlığını adetleriyle çarpar ve toplam molar kütleyi g/mol cinsinden verir. Örn: H2O için 2×H + 1×O."
                elif 'ph' in context_tool:
                    response = "pH Hesaplayıcı, H+ iyon derişimine göre pH = -log10[H+] ilişkisini kullanır. Gerektiğinde pOH ve pH+pOH=14 bağıntısı uygulanır."
                elif 'ideal gaz' in context_tool:
                    response = "İdeal Gaz Yasası hesaplayıcısı, PV=nRT denklemini kullanır. Bilinen değişkenlerden bilinmeyeni çözer ve birimleri dönüştürür."
            elif intent == 'example' and context_tool:
                if 'molekül' in context_tool:
                    response = "Örnek: C6H12O6 için 6×C + 12×H + 6×O toplamı alınır. Parantezli örnek: Ca(OH)2 ⇒ Ca + 2×O + 2×H."
                elif 'ph' in context_tool:
                    response = "Örnek: [H+] = 1×10^-3 M ⇒ pH = 3. Eğer pOH gerekiyorsa pOH = 14 - pH."
                elif 'ideal gaz' in context_tool:
                    response = "Örnek: P=1 atm, V=22.4 L, T=273.15 K ise n ≈ 1 mol. R uygun birim seçimiyle kullanılır."
            elif intent == 'validate' and context_tool:
                if 'molekül' in context_tool:
                    response = "Formül doğrulama: Büyük/küçük harfe dikkat edin (Ca, Cl). Geçersiz sembol veya dengesiz parantez hata üretir."
                else:
                    response = "Girdi birimlerini ve aralıklarını kontrol edin. Boş alan bırakmayın, sayı ve işaretleri doğru girin."
            elif intent == 'tips_formula':
                response = "İpuçları: Elementler büyük harfle başlar (Na, Fe, Co). Parantez sonrası sayı tüm gruba uygulanır. Örn: Al2(SO4)3."
            elif intent == 'symbols':
                response = "Yaygın semboller: H, C, N, O, Na, K, Ca, Cl, Fe, Cu, Zn, S, P. Sembolleri doğru harflerle yazın."
            elif intent == 'ph_poh':
                response = "pH ve pOH ilişkisi: pH + pOH = 14 (25°C). [H+][OH-] = 1×10^-14. pOH = -log10[OH-]."
            elif intent == 'example_ph':
                response = "Örnek: [OH-] = 1×10^-5 M ⇒ pOH = 5 ⇒ pH = 9."
            
            if 'merhaba' in message or 'selam' in message:
                response = "Merhaba! Ben ChemAI. Kimya ile ilgili sana nasıl yardımcı olabilirim?"
            elif 'kimya' in message:
                response = "Kimya, maddenin yapısını, özelliklerini, bileşimini, etkileşimlerini ve tepkimelerini inceleyen bilim dalıdır. Hangi konuda detaya girmemi istersin?"
            elif 'atom' in message:
                response = "Atom, bir elementin tüm kimyasal özelliklerini taşıyan en küçük yapı taşıdır. Proton, nötron ve elektronlardan oluşur."
            elif 'molekül' in message:
                response = "Molekül, iki veya daha fazla atomun kimyasal bağlarla bir arada tutulmasıyla oluşan, elektriksel olarak nötr en küçük birimdir."
            elif 'ph' in message:
                response = "pH, bir çözeltinin asitlik veya bazlık derecesini tarif eden bir ölçü birimidir. 0-7 arası asidik, 7 nötr, 7-14 arası baziktir."
            elif 'mol' in message:
                response = "Mol, 6.022 x 10^23 (Avogadro sayısı) kadar tanecik içeren madde miktarıdır. Kimyada madde miktarını ifade etmek için kullanılır."
            elif 'periyodik' in message:
                response = "Periyodik tablo, kimyasal elementlerin atom numarası, elektron dizilimi ve tekrarlayan kimyasal özelliklerine göre sıralandığı bir çizelgedir."
            elif 'su' in message or 'h2o' in message:
                response = "Su (H2O), iki hidrojen ve bir oksijen atomundan oluşan, yaşam için vazgeçilmez bir moleküldür. Standart koşullarda sıvıdır."
            elif 'asit' in message:
                response = "Asitler, sulu çözeltilerine H+ iyonu veren maddelerdir. Tatları ekşidir ve mavi turnusol kağıdını kırmızıya çevirirler."
            elif 'baz' in message:
                response = "Bazlar, sulu çözeltilerine OH- iyonu veren maddelerdir. Tatları acıdır, ele kayganlık hissi verirler ve kırmızı turnusol kağıdını maviye çevirirler."
            elif 'gaz' in message:
                response = "Gazlar, molekülleri birbirinden bağımsız hareket eden ve bulundukları kabı tamamen dolduran madde halidir. İdeal gaz yasası (PV=nRT) ile tanımlanırlar."
            else:
                # Default responses if no keyword matches
                defaults = [
                    "Bu konu hakkında daha fazla detay verebilir misin? Kimya veritabanımı tarıyorum...",
                    "Çok ilginç bir soru! Ancak şu an tam olarak anlayamadım. Biraz daha spesifik olabilir misin?",
                    "Bu konuda bir hesaplama yapmak istersen 'Araçlar' menüsündeki hesaplayıcıları kullanabilirsin.",
                    "Kimya çok geniş bir alan. Atomlar, moleküller, tepkimeler veya periyodik tablo hakkında sorabilirsin."
                ]
                response = random.choice(defaults)

            return JsonResponse({'response': response})
        except Exception as e:
            return JsonResponse({'response': 'Bir hata oluştu. Lütfen tekrar deneyin.'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def home(request):
    return render(request, 'home.html')

def molecular_weight(request):
    return render(request, 'calculators/molecular_weight.html')

def molarity(request):
    return render(request, 'calculators/molarity.html')

def ph_calculator(request):
    return render(request, 'calculators/ph_calculator.html')

def ideal_gas(request):
    return render(request, 'calculators/ideal_gas.html')

def calculator_list(request):
    return render(request, 'calculators/calculator_list.html')

def percent_yield(request):
    return render(request, 'calculators/percent_yield.html')

def half_life(request):
    return render(request, 'calculators/half_life.html')

def boyles_law(request):
    return render(request, 'calculators/boyles_law.html')

def dilution_factor(request):
    return render(request, 'calculators/dilution_factor.html')

def mass_percent(request):
    return render(request, 'calculators/mass_percent.html')

def mixing_ratio(request):
    return render(request, 'calculators/mixing_ratio.html')

def serial_dilution(request):
    return render(request, 'calculators/serial_dilution.html')

def solution_dilution(request):
    return render(request, 'calculators/solution_dilution.html')

def neutralization(request):
    return render(request, 'calculators/neutralization.html')
def buffer_capacity(request):
    return render(request, 'calculators/buffer_capacity.html')
def nernst_equation(request):
    return render(request, 'calculators/nernst_equation.html')
def ionic_strength(request):
    return render(request, 'calculators/ionic_strength.html')
def electrolysis(request):
    return render(request, 'calculators/electrolysis.html')
def chemical_name(request):
    return render(request, 'calculators/chemical_name.html')
def effective_nuclear_charge(request):
    return render(request, 'calculators/effective_nuclear_charge.html')
def electron_configuration(request):
    return render(request, 'calculators/electron_configuration.html')
def electronegativity(request):
    return render(request, 'calculators/electronegativity.html')
def activation_energy(request):
    return render(request, 'calculators/activation_energy.html')
def arrhenius(request):
    return render(request, 'calculators/arrhenius.html')
def equilibrium_constant(request):
    return render(request, 'calculators/equilibrium_constant.html')
def kp_constant(request):
    return render(request, 'calculators/kp.html')
def actual_yield(request):
    return render(request, 'calculators/actual_yield.html')
def register_page(request):
    return render(request, 'register.html')

def login_page(request):
    return render(request, 'login.html')

def api_register(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        if not username or not email or not password:
            return JsonResponse({'error': 'Missing fields'}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)
        user = User.objects.create_user(username=username, email=email, password=password)
        token = _generate_token(user.id, user.username)
        return JsonResponse({'token': token, 'user': {'id': user.id, 'username': user.username, 'email': user.email}})
    except Exception:
        return JsonResponse({'error': 'Registration failed'}, status=500)

def api_login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        auth_username = username
        if not auth_username and email:
            try:
                user = User.objects.get(email=email)
                auth_username = user.username
            except User.DoesNotExist:
                auth_username = ''
        user = authenticate(request, username=auth_username, password=password)
        if not user:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
        token = _generate_token(user.id, user.username)
        return JsonResponse({'token': token, 'user': {'id': user.id, 'username': user.username, 'email': user.email}})
    except Exception:
        return JsonResponse({'error': 'Login failed'}, status=500)

def api_me(request):
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    try:
        token = auth.split(' ', 1)[1]
        payload = _verify_token(token)
        if not payload:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        user = User.objects.get(id=payload.get('sub'))
        return JsonResponse({'id': user.id, 'username': user.username, 'email': user.email})
    except User.DoesNotExist:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    except Exception:
        return JsonResponse({'error': 'Server error'}, status=500)

def forum_home(request):
    categories = Category.objects.all().order_by('name')
    q = request.GET.get('q', '').strip()
    c = request.GET.get('c', '').strip()
    sort = request.GET.get('sort', 'latest').strip()
    try:
        page = max(1, int(request.GET.get('page', '1')))
    except ValueError:
        page = 1
    try:
        page_size = max(1, min(50, int(request.GET.get('page_size', '20'))))
    except ValueError:
        page_size = 20
    threads = Thread.objects.filter(is_deleted=False)
    if c:
        threads = threads.filter(category__slug=c)
    if q:
        threads = threads.filter(Q(title__icontains=q) | Q(content__icontains=q))
    if sort == 'active':
        threads = threads.order_by('-updated_at')
    elif sort == 'top':
        threads = threads.annotate(ac=Count('answers')).order_by('-ac', '-created_at')
    else:
        threads = threads.order_by('-created_at')
    total = threads.count()
    start = (page - 1) * page_size
    end = start + page_size
    threads = threads.select_related('author', 'category')[start:end]
    has_next = end < total
    return render(request, 'forum.html', {'categories': categories, 'threads': threads, 'q': q, 'c': c, 'sort': sort, 'page': page, 'page_size': page_size, 'has_next': has_next})

@csrf_exempt
def api_forum_threads(request):
    if request.method == 'GET':
        q = request.GET.get('q', '').strip()
        c = request.GET.get('c', '').strip()
        sort = request.GET.get('sort', 'latest').strip()
        try:
            page = max(1, int(request.GET.get('page', '1')))
        except ValueError:
            page = 1
        try:
            page_size = max(1, min(50, int(request.GET.get('page_size', '20'))))
        except ValueError:
            page_size = 20
        qs = Thread.objects.filter(is_deleted=False)
        if c:
            qs = qs.filter(category__slug=c)
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
        if sort == 'active':
            qs = qs.order_by('-updated_at')
        elif sort == 'top':
            qs = qs.annotate(ac=Count('answers')).order_by('-ac', '-created_at')
        else:
            qs = qs.order_by('-created_at')
        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size
        data = []
        for t in qs.select_related('author', 'category')[start:end]:
            data.append({
                'id': t.id,
                'title': t.title,
                'content': t.content[:300],
                'category': {'name': t.category.name, 'slug': t.category.slug},
                'author': t.author.username,
                'created_at': t.created_at.isoformat(),
                'answers_count': t.answers.filter(is_deleted=False).count(),
            })
        return JsonResponse({'threads': data, 'page': page, 'page_size': page_size, 'total': total, 'has_next': end < total})
    if request.method == 'POST':
        try:
            auth = request.headers.get('Authorization', '')
            if not auth.startswith('Bearer '):
                return JsonResponse({'error': 'Unauthorized'}, status=401)
            payload = _verify_token(auth.split(' ', 1)[1])
            if not payload:
                return JsonResponse({'error': 'Unauthorized'}, status=401)
            user = User.objects.get(id=payload.get('sub'))
            body = json.loads(request.body)
            title = body.get('title', '').strip()
            content = body.get('content', '').strip()
            cat_slug = body.get('category', '').strip()
            if not title or not content or not cat_slug:
                return JsonResponse({'error': 'Missing fields'}, status=400)
            try:
                cat = Category.objects.get(slug=cat_slug)
            except Category.DoesNotExist:
                return JsonResponse({'error': 'Invalid category'}, status=400)
            t = Thread.objects.create(title=title, content=content, category=cat, author=user)
            return JsonResponse({'id': t.id})
        except Exception:
            return JsonResponse({'error': 'Create failed'}, status=500)
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def api_forum_answers(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    try:
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        payload = _verify_token(auth.split(' ', 1)[1])
        if not payload:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        user = User.objects.get(id=payload.get('sub'))
        body = json.loads(request.body)
        thread_id = body.get('thread_id')
        content = body.get('content', '').strip()
        if not thread_id or not content:
            return JsonResponse({'error': 'Missing fields'}, status=400)
        try:
            t = Thread.objects.get(id=thread_id, is_deleted=False)
        except Thread.DoesNotExist:
            return JsonResponse({'error': 'Thread not found'}, status=404)
        a = Answer.objects.create(thread=t, content=content, author=user)
        return JsonResponse({'id': a.id})
    except Exception:
        return JsonResponse({'error': 'Answer failed'}, status=500)

@csrf_exempt
def api_forum_vote_answer(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    try:
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        payload = _verify_token(auth.split(' ', 1)[1])
        if not payload:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        user = User.objects.get(id=payload.get('sub'))
        body = json.loads(request.body)
        answer_id = body.get('answer_id')
        if not answer_id:
            return JsonResponse({'error': 'Missing fields'}, status=400)
        try:
            a = Answer.objects.get(id=answer_id, is_deleted=False)
        except Answer.DoesNotExist:
            return JsonResponse({'error': 'Answer not found'}, status=404)
        try:
            AnswerVote.objects.create(answer=a, user=user)
            a.votes = a.votes + 1
            a.save(update_fields=['votes'])
            return JsonResponse({'votes': a.votes, 'voted': True})
        except Exception:
            try:
                v = AnswerVote.objects.get(answer=a, user=user)
                v.delete()
                a.votes = max(0, a.votes - 1)
                a.save(update_fields=['votes'])
                return JsonResponse({'votes': a.votes, 'voted': False})
            except AnswerVote.DoesNotExist:
                return JsonResponse({'error': 'Vote failed'}, status=500)
    except Exception:
        return JsonResponse({'error': 'Vote failed'}, status=500)

@csrf_exempt
def api_forum_report(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    try:
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        payload = _verify_token(auth.split(' ', 1)[1])
        if not payload:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        user = User.objects.get(id=payload.get('sub'))
        body = json.loads(request.body)
        item_type = body.get('item_type', '').strip()
        item_id = body.get('item_id')
        reason = body.get('reason', '').strip()
        if item_type not in ['thread', 'answer'] or not item_id or not reason:
            return JsonResponse({'error': 'Missing fields'}, status=400)
        Report.objects.create(item_type=item_type, item_id=int(item_id), reason=reason, reporter=user)
        return JsonResponse({'ok': True})
    except Exception:
        return JsonResponse({'error': 'Report failed'}, status=500)
        return JsonResponse({'error': 'Unauthorized'}, status=401)
