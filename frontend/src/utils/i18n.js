import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      // Nav
      'nav.applications':  'My Applications',
      'nav.apply':         'New Application',
      'nav.notifications': 'Notifications',
      'nav.queue':         'Review Queue',
      'nav.all_apps':      'All Applications',
      'nav.dashboard':     'Dashboard',
      'nav.model':         'Model Metrics',
      'nav.users':         'Users',
      'nav.profile':       'Profile',
      'nav.logout':        'Logout',

      // Auth
      'auth.login':         'Sign In',
      'auth.register':      'Register',
      'auth.email':         'Email Address',
      'auth.password':      'Password',
      'auth.name':          'Full Name',
      'auth.signing_in':    'Signing in…',
      'auth.create_account':'Create Account',

      // Application
      'app.status.pending':       'Pending',
      'app.status.auto_approved': 'Auto Approved',
      'app.status.needs_review':  'Needs Review',
      'app.status.approved':      'Approved',
      'app.status.rejected':      'Rejected',

      // Schemes
      'scheme.OAP':          'Old Age Pension',
      'scheme.WP':           'Widow Pension',
      'scheme.DP':           'Disability Pension',
      'scheme.NOT_ELIGIBLE': 'Not Eligible',

      // Documents
      'doc.aadhaar':               'Aadhaar Card',
      'doc.bpl_card':              'BPL Card',
      'doc.death_certificate':     'Death Certificate',
      'doc.disability_certificate':'Disability Certificate',

      // Common
      'common.save':    'Save',
      'common.cancel':  'Cancel',
      'common.submit':  'Submit',
      'common.loading': 'Loading…',
      'common.prev':    '← Prev',
      'common.next':    'Next →',
      'common.view':    'View',
      'common.yes':     'Yes',
      'common.no':      'No',
    },
  },
  hi: {
    translation: {
      // Nav
      'nav.applications':  'मेरे आवेदन',
      'nav.apply':         'नया आवेदन',
      'nav.notifications': 'सूचनाएँ',
      'nav.queue':         'समीक्षा कतार',
      'nav.all_apps':      'सभी आवेदन',
      'nav.dashboard':     'डैशबोर्ड',
      'nav.model':         'मॉडल मेट्रिक्स',
      'nav.users':         'उपयोगकर्ता',
      'nav.profile':       'प्रोफ़ाइल',
      'nav.logout':        'लॉग आउट',

      // Auth
      'auth.login':         'साइन इन करें',
      'auth.register':      'पंजीकरण करें',
      'auth.email':         'ईमेल पता',
      'auth.password':      'पासवर्ड',
      'auth.name':          'पूरा नाम',
      'auth.signing_in':    'साइन इन हो रहा है…',
      'auth.create_account':'खाता बनाएं',

      // Application
      'app.status.pending':       'लंबित',
      'app.status.auto_approved': 'स्वतः स्वीकृत',
      'app.status.needs_review':  'समीक्षा आवश्यक',
      'app.status.approved':      'स्वीकृत',
      'app.status.rejected':      'अस्वीकृत',

      // Schemes
      'scheme.OAP':          'वृद्धावस्था पेंशन',
      'scheme.WP':           'विधवा पेंशन',
      'scheme.DP':           'विकलांगता पेंशन',
      'scheme.NOT_ELIGIBLE': 'पात्र नहीं',

      // Documents
      'doc.aadhaar':               'आधार कार्ड',
      'doc.bpl_card':              'बीपीएल कार्ड',
      'doc.death_certificate':     'मृत्यु प्रमाण पत्र',
      'doc.disability_certificate':'विकलांगता प्रमाण पत्र',

      // Common
      'common.save':    'सहेजें',
      'common.cancel':  'रद्द करें',
      'common.submit':  'जमा करें',
      'common.loading': 'लोड हो रहा है…',
      'common.prev':    '← पिछला',
      'common.next':    'अगला →',
      'common.view':    'देखें',
      'common.yes':     'हाँ',
      'common.no':      'नहीं',
    },
  },
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: localStorage.getItem('lang') || 'en',
    fallbackLng: 'en',
    interpolation: { escapeValue: false },
  });

export default i18n;