import { Injectable, signal } from '@angular/core';

export interface AnonymizationResult {
  sanitizedText: string;
  maskedCount: number;
  detectedTypes: string[];
}

@Injectable({
  providedIn: 'root'
})
export class PiiAnonymizerService {
  // Global toggle for PII Protection Shield
  isPiiShieldActive = signal<boolean>(true);

  toggleShield(): void {
    this.isPiiShieldActive.update(v => !v);
  }

  anonymize(text: string): AnonymizationResult {
    if (!text || !this.isPiiShieldActive()) {
      return { sanitizedText: text || '', maskedCount: 0, detectedTypes: [] };
    }

    let sanitized = text;
    let count = 0;
    const detected: Set<string> = new Set();

    // 1. Mask Tunisian CIN (8 digits e.g. 08123456 -> 08****56)
    const cinRegex = /\b(\d{2})\d{4}(\d{2})\b/g;
    if (cinRegex.test(sanitized)) {
      sanitized = sanitized.replace(cinRegex, (match, p1, p2) => {
        count++;
        detected.add('CIN Tunisienne');
        return `${p1}****${p2}`;
      });
    }

    // 2. Mask Tunisian RIB (20 digits e.g. 04 001 0000000000000 45)
    const ribRegex = /\b(04\s*\d{3})\s*[\d\s]{10,13}(\d{2})\b/g;
    if (ribRegex.test(sanitized)) {
      sanitized = sanitized.replace(ribRegex, (match, p1, p2) => {
        count++;
        detected.add('RIB Bancaire');
        return `${p1} *********** ${p2}`;
      });
    }

    // 3. Mask Email addresses
    const emailRegex = /([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)/g;
    if (emailRegex.test(sanitized)) {
      sanitized = sanitized.replace(emailRegex, (match, p1, p2) => {
        count++;
        detected.add('Adresse E-mail');
        return `${p1.slice(0, 2)}***@${p2}`;
      });
    }

    // 4. Mask Phone numbers (e.g. +216 98 123 456 or 22 345 678)
    const phoneRegex = /(?:\+216\s*)?([2597]\d)[\s.-]?\d{3}[\s.-]?\d{3}\b/g;
    if (phoneRegex.test(sanitized)) {
      sanitized = sanitized.replace(phoneRegex, (match, p1) => {
        count++;
        detected.add('N° Téléphone');
        return `+216 ${p1} *** ***`;
      });
    }

    return {
      sanitizedText: sanitized,
      maskedCount: count,
      detectedTypes: Array.from(detected)
    };
  }
}
