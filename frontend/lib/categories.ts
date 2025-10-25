// Shared category configuration for persona display

export const CATEGORY_INFO: Record<string, { title: string; description: string; color: string }> = {
  theologians: {
    title: 'Theologians',
    description: 'Religious thinkers and theologians',
    color: 'linear-gradient(to right, #f43f5e, #ec4899)',
  },
  philosophers: {
    title: 'Philosophers',
    description: 'Secular philosophers and thinkers',
    color: 'linear-gradient(to right, #6366f1, #a855f7)',
  },
  scientists: {
    title: 'Scientists',
    description: 'Scientific figures and researchers',
    color: 'linear-gradient(to right, #10b981, #14b8a6)',
  },
  ancient_schools: {
    title: 'Ancient Schools',
    description: 'Thinkers from ancient philosophical traditions',
    color: 'linear-gradient(to right, #f59e0b, #f97316)',
  },
  eastern_philosophers: {
    title: 'Eastern Philosophers',
    description: 'Philosophical traditions from Asia',
    color: 'linear-gradient(to right, #9333ea, #c026d3)',
  },
  mystics: {
    title: 'Mystics',
    description: 'Mystical and contemplative thinkers',
    color: 'linear-gradient(to right, #06b6d4, #0891b2)',
  },
  artists: {
    title: 'Artists',
    description: 'Creative thinkers and artists',
    color: 'linear-gradient(to right, #ec4899, #f472b6)',
  },
  political_theorists: {
    title: 'Political Theorists',
    description: 'Political philosophy and theory',
    color: 'linear-gradient(to right, #14b8a6, #0d9488)',
  },
  social_reformers: {
    title: 'Social Reformers',
    description: 'Activists and social change leaders',
    color: 'linear-gradient(to right, #f97316, #fb923c)',
  },
  economists: {
    title: 'Economists',
    description: 'Economic thinkers and theorists',
    color: 'linear-gradient(to right, #3b82f6, #2563eb)',
  },
  psychologists: {
    title: 'Psychologists',
    description: 'Pioneers of psychological thought',
    color: 'linear-gradient(to right, #84cc16, #65a30d)',
  },
  environmental_thinkers: {
    title: 'Environmental Thinkers',
    description: 'Environmental philosophy and ecology',
    color: 'linear-gradient(to right, #d946ef, #c026d3)',
  },
};

export function getCategoryInfo(categoryKey: string): { title: string; description: string; color: string } {
  return CATEGORY_INFO[categoryKey] || {
    title: categoryKey.charAt(0).toUpperCase() + categoryKey.slice(1).replace(/_/g, ' '),
    description: `Thinkers in ${categoryKey.replace(/_/g, ' ')}`,
    color: 'linear-gradient(to right, #6366f1, #a855f7)',
  };
}

// Sort personas by birth year (earliest first), then alphabetically by name
export function sortPersonasByTime<T extends { birth_year?: number | null; name: string }>(personas: T[]): T[] {
  return [...personas].sort((a, b) => {
    // First, sort by birth year (earlier birth years first)
    if (a.birth_year && b.birth_year) {
      if (a.birth_year !== b.birth_year) {
        return a.birth_year - b.birth_year;
      }
    } else if (a.birth_year) {
      return -1; // a has birth year, b doesn't - a comes first
    } else if (b.birth_year) {
      return 1; // b has birth year, a doesn't - b comes first
    }

    // If birth years are equal or both null/undefined, sort alphabetically by name
    return a.name.localeCompare(b.name);
  });
}

// Era/Time period classification
export type Era = 'ancient' | 'medieval' | 'early_modern' | 'modern' | 'contemporary';

export const ERA_INFO: Record<Era, { label: string; description: string; range: string }> = {
  ancient: {
    label: 'Ancient',
    description: 'Before 500 CE',
    range: 'Before 500 CE',
  },
  medieval: {
    label: 'Medieval',
    description: '500-1500 CE',
    range: '500-1500 CE',
  },
  early_modern: {
    label: 'Early Modern',
    description: '1500-1800 CE',
    range: '1500-1800 CE',
  },
  modern: {
    label: 'Modern',
    description: '1800-1950 CE',
    range: '1800-1950 CE',
  },
  contemporary: {
    label: 'Contemporary',
    description: '1950-Present',
    range: '1950-Present',
  },
};

// Classify persona into era based on birth year
export function getPersonaEra(birthYear: number | null | undefined): Era | null {
  if (!birthYear) return null;

  if (birthYear < 500) return 'ancient';
  if (birthYear < 1500) return 'medieval';
  if (birthYear < 1800) return 'early_modern';
  if (birthYear < 1950) return 'modern';
  return 'contemporary';
}
