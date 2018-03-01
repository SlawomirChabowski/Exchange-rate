# -*- coding: utf-8 -*-

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QPushButton,
                             QLabel, QGridLayout,
                             QLineEdit, QApplication,
                             QListWidget, QListWidgetItem)
import urllib.request, json
import datetime as dt
import numpy as np
import matplotlib.pyplot as plt

#zmienienie fontu w celu wyświetlania polskich znaków na wykresach
plt.rc('font', **{'sans-serif' : 'Arial', 'family' : 'sans-serif'})



#pobranie pliku json i otworzenie go
file = urllib.request.urlopen('http://api.nbp.pl/api/exchangerates/tables/a/last/30?format=json').read().decode('utf8')
values = json.loads(file)
"""
Pobrany plik w formacie json zawiera kursy
konkretnych walut obliczane nie codziennie,
ale kilka razy w tygodniu.
"""



#interpolacja wielomianowa metodą Lagrange-a
def interpolacja_lagrange(x, y, xval):
    """
    x - argument funkcji
    y - wartość funkcji
    xval - wartość interpolowana funkcji
    """
    products = 0
    yval = 0
    for i in range(len(x)):
        products = y[i]
        for j in range(len(x)):
            if i != j:
                products = products * (xval - x[j]) / (x[i] - x[j])
        yval = yval + products
    return yval



#aproksymacja i wykres
def swapRows(v,i,j):
    if len(v.shape) == 1:
        v[i],v[j] = v[j],v[i]
    else:
        v[[i,j],:] = v[[j,i],:]
     
        
        
def swapCols(v,i,j):
    v[:,[i,j]] = v[:,[j,i]]

    
    
def gaussPivot(a, b, tol = 1.0e12):
    n = len(b)
    s = np.zeros(n)
    for i in range(n):
        s[i] = max(np.abs(a[i,:]))
    
    for k in range(0, n-1):
        p = np.argmax(np.abs(a[k:n, k])/s[k:n])+k
        if abs(a[p, k])<tol:
            #print('Matrix is singular')
            pass
        if p != k:
            swapRows(b, k, p)
            swapRows(s, k, p)
            swapRows(a, k, p)
        
        for i in range(k+1, n):
            if a[i, k] != 0.0:
                lam = a[i, k]/a[k, k]
                a[i, k+1:n] = a[i, k+1:n]-lam*a[k, k+1:n]
                b[i] = b[i]-lam*b[k]
        
    if abs(a[n-1, n-1])<tol:
        #print('Matrix is singular')
        pass
    
    b[n-1] = b[n-1]/a[n-1, n-1]
    for k in range(n-2, -1, -1):
        b[k] = (b[k]-np.dot(a[k, k+1:n], b[k+1:n]))/a[k, k]
    
    return b
    
    

def polyFit(xData, yData, m):
    a = np.zeros((m+1, m+1))
    b = np.zeros(m+1)
    s = np.zeros(2*m+1)
    
    for i in range(len(xData)):
        temp = yData[i]
        for j in range(m+1):
            b[j] = b[j]+temp
            temp = temp*xData[i]
        temp = 1.0
        for j in range(2*m+1):
            s[j] = s[j]+temp
            temp = temp*xData[i]
    
    for i in range(m+1):
        for j in range(m+1):
            a[i, j] = s[i+j]
    
    return gaussPivot(a, b)

    
    
def plotPoly(title, xData, yData, coeff, xlab = 'Okres (w dniach)', ylab = 'Kurs waluty (w stosunku do PLN)'):
    m = len(coeff)
    x1 = min(xData)
    x2 = max(xData)
    dx = (x2-x1)/20.0 #wyliczenie kroku
    x = np.arange(x1, x2+dx/10.0, dx)
    y = np.zeros((len(x)))*1.0
    for i in range(m): #obliczanie wielomianu
        y = y+coeff[i]*x**i
    plt.figure('Kurs walut - '+title+' (autor: Sławomir Chabowski)')
    plt.clf()
    plt.plot(xData, yData, '.--', label = u'Wartości domyślne')
    plt.plot(x, y, '-r', label = u'Wartości zaokrąglone (aproksymowane)')
    plt.legend()
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15),
          fancybox=True, shadow=True, ncol=5)
    plt.xlabel(xlab); plt.ylabel(ylab)
    plt.grid(True)
    plt.title(title)
    plt.show()



opis = """
Wybierz dowolną walutę z
listy po lewej - zostaną
wtedy wyświetlone jej
kursy w ubiegłych oraz
obecnych dniach, wykres
(z zestawioną funkcją
przewidywania kursów
oraz przewidywane kursy
na kilka kolejnych dni.

W dniach, kiedy nie wy-
konywano pomiaru kursu
waluty, obliczone zosta-
ły jej wartości interpo-
lowane (oznaczone
znakiem "*".)
"""+29*'\n'



class Program(QWidget):
    
    def __init__(self):
        super().__init__()

        
        self.lbl1 = QLabel('Wybierz walutę:'+55*' ')
        self.lbl2 = QLabel('Instrukcja:'+20*' ')
        self.lbl3 = QLabel(opis)
        self.btn1 = QPushButton('Wybierz')
        self.btn2 = QPushButton('Pomoc')
        self.list = QListWidget()
        for i in range(len(values[0]['rates'])):
            item = QListWidgetItem('%s (%s)' % (values[0]['rates'][i]['code'], values[0]['rates'][i]['currency']))
            self.list.addItem(item)
        
 
        #siatka
        siatka = QGridLayout()
        siatka.setSpacing(10)

        siatka.addWidget(self.lbl1, 0, 0)
        siatka.addWidget(self.list, 1, 0)
        siatka.addWidget(self.btn1, 2, 0)
        
        siatka.addWidget(self.lbl2, 0, 1)
        siatka.addWidget(self.lbl3, 1, 1)
        siatka.addWidget(self.btn2, 2, 1)
        
        self.setLayout(siatka)#włącz siatkę

        #łączy zdarzenie przyciśnięcia przycisku z funkcją zaznaczenie()
        #pobiera indeks waluty
        self.btn1.clicked.connect(self.zaznaczenie)

        #zdarzenie przyciśnięcia przycisku pomocy
        self.btn2.clicked.connect(self.pomoc)
        
        self.setGeometry(300, 300, 100, 100)
        #szerokość 100 pozwala na dobranie minimalnej szerokości i wysokości okna
        self.setWindowTitle('Kurs walut (autor: Sławomir Chabowski)')
        self.show()

    def zaznaczenie(self):
        sender = self.sender()
        a = self.list.currentRow()
        print('Wybrana waluta: %s' %values[0]['rates'][a]['code'])

        temp = []
        yappr = []
        for i in range(len(values)):
            roznica_dni = (dt.datetime.strptime(values[i]['effectiveDate'], '%Y-%m-%d') - dt.datetime.strptime(values[i-1]['effectiveDate'], '%Y-%m-%d')).days
            if roznica_dni>1:
                j=0
                y = [values[i-1]['rates'][a]['mid'], values[i]['rates'][a]['mid']]
                x = [i for i in range(len(y))]
                xval = [i for i in np.arange(0, 1, 1/roznica_dni)]
                yval = []
                ytemp = []
                print('Wyliczanie interpolacji w dniach: %s - %s' % (values[i-1]['effectiveDate'], values[i]['effectiveDate']))
                for xv in xval:
                    data = (dt.datetime.strptime(values[i]['effectiveDate'], '%Y-%m-%d')-dt.timedelta(days=roznica_dni-j)).__format__('%Y-%m-%d')
                    yval.append ('%s:*    %.4f\n' % (data, interpolacja_lagrange(x, y, xv)))
                    ytemp.append(interpolacja_lagrange(x, y, xv))
                    j+=1
                for j in range(1, len(yval)):
                    temp.append(yval[j])
                    yappr.append(ytemp[j])
                temp.append ('%s:      %.4f\n' % (values[i]['effectiveDate'], values[i]['rates'][a]['mid']))
                yappr.append (values[i]['rates'][a]['mid'])
            else:
                yappr.append (values[i]['rates'][a]['mid'])
                temp.append ('%s:      %.4f\n' % (values[i]['effectiveDate'], values[i]['rates'][a]['mid']))
        print(30*'-')
        temp.reverse()
        text = ''.join(temp)
        self.lbl3.setText(text)
        self.lbl2.setText('Kurs wybranej waluty:')
        xappr = [i for i in range(0, len(yappr))]
        coeff = polyFit(xappr, yappr, 5)
        plotPoly('Kurs '+values[0]['rates'][a]['code'], xappr, yappr, coeff)

        
    def pomoc(self):
        """
        Przycisk pomoc resetuje treść
        drugiej kolumny
        """
        self.lbl2.setText('Instrukcja:'+20*' ')
        sender = self.sender()
        self.lbl3.setText(opis)        

        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Program()
    sys.exit(app.exec_())
