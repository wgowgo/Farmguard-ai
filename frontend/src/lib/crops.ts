import type { CropProfile } from '@/lib/api';

/** 백엔드 구버전, 미기동 시 UI 폴백 (crops.json과 동기화) */
export const FALLBACK_CROPS: CropProfile[] = [
  { id: 'pepper', name_ko: '고추', soil_code: '00013', category: '채소', season: 'summer', target_pests: ['탄저병', '역병', '담배나방'] },
  { id: 'tomato', name_ko: '토마토', soil_code: '00013', category: '채소', season: 'summer', target_pests: ['잿빛곰팡이병', '역병', '담배가루이'] },
  { id: 'strawberry', name_ko: '딸기', soil_code: '00013', category: '채소', season: 'winter', target_pests: ['잿빛곰팡이병', '흰가루병', '응애'] },
  { id: 'rice', name_ko: '벼', soil_code: '00001', category: '곡물', season: 'summer', target_pests: ['도열병', '잎마름병', '벼멸구'] },
  { id: 'cucumber', name_ko: '오이', soil_code: '00013', category: '채소', season: 'summer', target_pests: ['노균병', '탄저병', '응애'] },
  { id: 'eggplant', name_ko: '가지', soil_code: '00013', category: '채소', season: 'summer', target_pests: ['탄저병', '흰가루병', '담배가루이'] },
  { id: 'apple', name_ko: '사과', soil_code: '00013', category: '과수', season: 'year_round', target_pests: ['검은점병', '탄저병', '응애'] },
  { id: 'grape', name_ko: '포도', soil_code: '00013', category: '과수', season: 'summer', target_pests: ['탄저병', '노균병', '응애'] },
  { id: 'garlic', name_ko: '마늘', soil_code: '00021', category: '채소', season: 'winter', target_pests: ['자주무늬병', '총채벌레'] },
  { id: 'onion', name_ko: '양파', soil_code: '00022', category: '채소', season: 'winter', target_pests: ['자주무늬병', '파총채벌레'] },
  { id: 'soybean', name_ko: '콩', soil_code: '00013', category: '곡물', season: 'summer', target_pests: ['탄저병', '진딧물'] },
  { id: 'corn', name_ko: '옥수수', soil_code: '00013', category: '곡물', season: 'summer', target_pests: ['세균성줄무늬병', '옥수수나방'] },
];

export async function loadCrops(fetcher: () => Promise<{ crops: CropProfile[] }>): Promise<CropProfile[]> {
  try {
    const r = await fetcher();
    return r.crops?.length ? r.crops : FALLBACK_CROPS;
  } catch {
    return FALLBACK_CROPS;
  }
}
