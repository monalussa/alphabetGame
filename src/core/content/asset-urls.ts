import { isLanguageCode, isSafeId } from './parse-pack';

const PACKS_PATH = 'packs';
const AUDIO_EXTENSION = '.mp3';
const IMAGE_EXTENSION = '.svg';

function requireId(value: string, isValid: (value: string) => boolean): string {
  if (!isValid(value)) throw new Error(`Refusing to build an asset URL from '${value}'`);
  return value;
}

export function createAssetUrls(baseUrl: string) {
  const base = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
  const pack = (code: string) => `${base}${PACKS_PATH}/${requireId(code, isLanguageCode)}`;

  return {
    packIndex: () => `${base}${PACKS_PATH}/index.json`,
    pack: (code: string) => `${pack(code)}.json`,
    clip: (code: string, clipId: string) =>
      `${pack(code)}/audio/${requireId(clipId, isSafeId)}${AUDIO_EXTENSION}`,
    character: (code: string, characterId: string) =>
      `${pack(code)}/characters/${requireId(characterId, isSafeId)}${IMAGE_EXTENSION}`,
    image: (imageId: string) => `${base}images/${requireId(imageId, isSafeId)}${IMAGE_EXTENSION}`,
    funSound: (soundId: string) =>
      `${base}sounds/${requireId(soundId, isSafeId)}${AUDIO_EXTENSION}`,
  };
}

export type AssetUrls = ReturnType<typeof createAssetUrls>;
