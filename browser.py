# -*- coding: utf-8 -*-

# Copyright(C) 2013  Romain Bignon
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.


import urllib
import re
import mechanize

from weboob.deprecated.browser import Browser, BrowserIncorrectPassword
from weboob.tools.date import LinearDateGuesser
from weboob.capabilities.bank import Transfer, TransferError
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
from shutil import rmtree

from datetime import datetime

from .pages import HomePage, LoginPage, LoginErrorPage, AccountsPage, \
                   TransferPage, SavingsPage, TransactionsPage, UselessPage, CardsPage


__all__ = ['Cragr']


class Cragr(Browser):
    PROTOCOL = 'https'
    ENCODING = 'ISO-8859-1'

    PAGES = {'https?://[^/]+/':                                          HomePage,
		'https?://[^/]+/particuliers.html':                         HomePage,
             'https?://[^/]+/stb/entreeBam':                             LoginPage,
             'https?://[^/]+/stb/entreeBam\?.*typeAuthentification=CLIC_ALLER.*': LoginPage,
             'https?://[^/]+/stb/entreeBam\?.*pagePremVisite.*':         UselessPage,
             'https?://[^/]+/stb/entreeBam\?.*Interstitielle.*':         UselessPage,
             'https?://[^/]+/stb/entreeBam\?.*act=Tdbgestion':           UselessPage,
             'https?://[^/]+/stb/entreeBam\?.*act=Synthcomptes':         AccountsPage,
             'https?://[^/]+/stb/entreeBam\?.*act=Virementssepa':        TransferPage,
             'https?://[^/]+/stb/entreeBam\?.*act=Synthepargnes':        SavingsPage,
             'https?://[^/]+/stb/.*act=Releves.*':                       TransactionsPage,
             'https?://[^/]+/stb/collecteNI\?.*sessionAPP=Releves.*':    TransactionsPage,
             'https?://[^/]+/stb/.*/erreur/.*':                          LoginErrorPage,
             'https?://[^/]+/stb/entreeBam\?.*act=Messagesprioritaires': UselessPage,
             'https?://[^/]+/stb/collecteNI\?.*fwkaction=Cartes.*':      CardsPage,
             'https?://[^/]+/stb/collecteNI\?.*fwkaction=Detail.*sessionAPP=Cartes.*': CardsPage,
            }

    class WebsiteNotSupported(Exception):
        pass

    def __init__(self, website, *args, **kwargs):
        self.DOMAIN = re.sub('^m\.', 'www.', website)
        self.accounts_url = None
        Browser.__init__(self, *args, **kwargs)

    def home(self):
        self.login()

    def is_logged(self):
        return self.page is not None and not self.is_on_page(HomePage)

    def login(self):
        """
        Attempt to log in.
        Note: this method does nothing if we are already logged in.
        """
        assert isinstance(self.username, basestring)
        assert isinstance(self.password, basestring)

        # Do we really need to login?
        if self.is_logged():
            self.logger.debug('already logged in')
            return

        if not self.is_on_page(HomePage):
            self.location(self.absurl('/'), no_login=True)

        # On the homepage, we get the URL of the auth service.
        url = self.page.get_post_url()
        self.login_url = url
        if url is None:
            raise self.WebsiteNotSupported()

        # First, post account number to get the password prompt.
        data = {'CCPTE':                self.username.encode(self.ENCODING),
                'canal':                'WEB',
                'hauteur_ecran':        768,
                'largeur_ecran':        1024,
                'liberror':             '',
                'matrice':              'true',
                'origine':              'vitrine',
                'situationTravail':     'BANCAIRE',
                'typeAuthentification': 'CLIC_ALLER',
                'urlOrigine':           self.page.url,
                'vitrine':              0,
               }

        self.location(url, urllib.urlencode(data))

        assert self.is_on_page(LoginPage)

        # Then, post the password.
        self.page.login(self.password)

        # The result of POST is the destination URL.
        url = self.page.get_result_url()

        if not url.startswith('http'):
            raise BrowserIncorrectPassword(url)

        self.location(url)

        if self.is_on_page(LoginErrorPage):
            raise BrowserIncorrectPassword()

        if self.page is None:
            raise self.WebsiteNotSupported()

        if not self.is_on_page(AccountsPage):
            # Sometimes the home page is Releves.
            new_url  = re.sub('act=([^&=]+)', 'act=Synthcomptes', self.page.url, 1)
            self.location(new_url)

        if not self.is_on_page(AccountsPage):
            raise self.WebsiteNotSupported()

        # Store the current url to go back when requesting accounts list.
        self.accounts_url = self.page.url

        # we can deduce the URL to "savings" accounts from the regular accounts one
        self.savings_url  = re.sub('act=([^&=]+)', 'act=Synthepargnes', self.accounts_url, 1)

        # we can deduce the URL to "transfer"  from the regular accounts one
        self.transfer_url  = re.sub('act=([^&=]+)', 'act=Virementssepa', self.accounts_url, 1)

    def get_accounts_list(self):
        accounts_list = []
        # regular accounts
        if not self.is_on_page(AccountsPage):
            self.location(self.accounts_url)
        accounts_list.extend(self.page.get_list())

        # credit cards
        for cards_page in self.page.cards_pages():
            self.location(cards_page)
            assert self.is_on_page(CardsPage)
            accounts_list.extend(self.page.get_list())

        # savings accounts
        self.location(self.savings_url)
        if self.is_on_page(SavingsPage):
            for account in self.page.get_list():
                if account not in accounts_list:
                    accounts_list.append(account)
        return accounts_list

    def get_account(self, id):
        assert isinstance(id, basestring)

        l = self.get_accounts_list()
        for a in l:
            if a.id == ('%s' % id):
                return a

        return None

    def get_history(self, account):
        # some accounts may exist without a link to any history page
        if account._link is None:
            return

        date_guesser = LinearDateGuesser()
        self.location(account._link)

        if self.is_on_page(CardsPage):
            for tr in self.page.get_history(date_guesser):
                yield tr
        else:
            url = self.page.get_order_by_date_url()

            while url:
                self.location(url)
                assert self.is_on_page(TransactionsPage)

                for tr in self.page.get_history(date_guesser):
                    yield tr

                url = self.page.get_next_url()

    def get_transfer_accounts(self):
        if not self.is_on_page(TransferPage):
             self.location(self.transfer_url)

        assert self.is_on_page(TransferPage)
        return self.page.get_transfer_target_accounts()

    def selenium_start(self):
        # To avoid ImportError during e.g. building modules list.
        from selenium import webdriver

        WIDTH = 1920
        HEIGHT = 10000  # So that everything fits...

        prof = webdriver.FirefoxProfile()
        self._browser = webdriver.Firefox(prof)
        self._browser.set_window_size(WIDTH, HEIGHT)

        url= self.login_url
        data = {'CCPTE':                self.username.encode(self.ENCODING),
                'canal':                'WEB',
                'hauteur_ecran':        768,
                'largeur_ecran':        1024,
                'liberror':             '',
                'matrice':              'true',
                'origine':              'vitrine',
                'situationTravail':     'BANCAIRE',
                'typeAuthentification': 'CLIC_ALLER',
                'urlOrigine':           self.page.url,
                'vitrine':              0,
               }
        self._browser.get(url+'?'+urllib.urlencode(data))

        imgmap = {}
        self._browser.implicitly_wait(3)

        for td in self._browser.find_elements_by_xpath('//table[@id="pave-saisie-code"]/tbody/tr/td'):
            a = td.find_element_by_xpath('.//a')
            num = a.get_attribute("text").strip()
            if num.isdigit():
                imgmap[num] = int(a.get_attribute("tabindex")) - 1

        hidden1 = self._browser.find_element_by_name('CCCRYC')
        value1 = ','.join(['%02d' % imgmap[c] for c in self.password])
        self._browser.execute_script("arguments[0].value = '%s';"%value1,hidden1)
        hidden2 = self._browser.find_element_by_name('CCCRYC2')
        value2 = '0' * len(self.password)
        self._browser.execute_script("arguments[0].value = '%s';"%value2,hidden2)
        
        self._browser.execute_script("javascript:Valid()")
        try:
            element = WebDriverWait(self._browser, 10).until(
                EC.presence_of_element_located((By.ID, "btn-deconnexion"))
            )
        except:
            self.selenium_finish()

    def selenium_finish(self):
        prof_dir = self._browser.firefox_profile.profile_dir
        self._browser.close()
        del self._browser
        rmtree(prof_dir)

    def do_transfer(self, account, to, amount, reason=None):
        """
            Transfer the given amount of money from an account to another,
            tagging the transfer with the given reason.
        """
        
        self.selenium_start()

        # access the transfer page

        transfer_page_unreachable_message = u'Could not reach the transfer page.'
        transfer_page_processerror_message = u'Error while processing the transfer.'
        #self._browser.get(self.absurl('/'))
        self.selenium_accounts_url = self._browser.current_url
        self.selenium_transfer_url = re.sub('act=([^&=]+)', 'act=Virementssepa', self.selenium_accounts_url, 1)
        self._browser.get(self.selenium_transfer_url)

        try:
            element = WebDriverWait(self._browser, 3).until(
                EC.presence_of_element_located((By.XPATH, '//*[text() ="Compte bénéficiaire :"]'))
            )
        except:
            self.selenium_finish()
            print(transfer_page_unreachable_message)
            raise

        # separate euros from cents
        amount_euros = int(amount)
        amount_cents = int((amount * 100) - (amount_euros * 100))


        try:
            element = WebDriverWait(self._browser, 3).until(
                EC.presence_of_element_located((By.XPATH, '//*[@name ="VIR_VIR1_FR3_LE"]'))
            )
            element = WebDriverWait(self._browser, 3).until(
                EC.presence_of_element_located((By.XPATH, '//*[@name ="VIR_VIR1_FR3_LB"]'))
            )
        except:
            self.selenium_finish()
            print(transfer_page_processerror_message)
            raise

        for option in Select(self._browser.find_element_by_name('VIR_VIR1_FR3_LE')).options:
            if account in option.text:
                Select(self._browser.find_element_by_name('VIR_VIR1_FR3_LE')).select_by_visible_text(option.text)
        
        for option in Select(self._browser.find_element_by_name('VIR_VIR1_FR3_LB')).options:
            if to in option.text:
                Select(self._browser.find_element_by_name('VIR_VIR1_FR3_LB')).select_by_visible_text(option.text)
        amount1 = self._browser.find_element_by_name('T3SEF_MTT_EURO')  
        self._browser.execute_script("arguments[0].value = '%s';"%amount_euros,amount1)
        amount2 = self._browser.find_element_by_name('T3SEF_MTT_CENT') 
        self._browser.execute_script("arguments[0].value = '%02d';"%amount_cents,amount2)
        
        #click on first step
        self._browser.execute_script("javascript:verif('Confirmer')")

        try:
            element = WebDriverWait(self._browser, 3).until(
                EC.presence_of_element_located((By.XPATH, '//*[@name ="VICrt_CDDOOR"]'))
            )
        except:
            self.selenium_finish()
            print(transfer_page_processerror_message)
            raise

        reason_elm = self._browser.find_element_by_name('VICrt_CDDOOR') 

        if not reason is None:
            self._browser.execute_script("arguments[0].value = '%s';"%reason,reason_elm)
        
        submit_date = datetime.now()

        self._browser.execute_script("javascript:verif('Confirmer')")
        
        try:
            element = WebDriverWait(self._browser, 3).until(
                EC.presence_of_element_located((By.XPATH, '//a[text() ="Confirmer"]'))
            )
        except:
            self.selenium_finish()
            print(transfer_page_processerror_message)
            raise

        self._browser.execute_script("javascript:verif('Confirmer')")

        try:
            element = WebDriverWait(self._browser, 3).until(
                EC.presence_of_element_located((By.XPATH, '//a[text() ="Nouveau virement"]'))
            )
        except:
            self.selenium_finish()
            print(transfer_page_processerror_message)
            raise

        # We now have to return a Transfer object
        # the final page does not provide any transfer id, so we'll use the submit date
        transfer = Transfer(submit_date.strftime('%Y%m%d%H%M%S'))
        transfer.amount = amount
        transfer.origin = account
        transfer.recipient = to
        transfer.date = submit_date
        self.selenium_finish()
        return transfer
