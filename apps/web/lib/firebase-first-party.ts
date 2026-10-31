import type {FirebaseOptions} from 'firebase/app';

/**
 * Feature-gated first-party Firebase OAuth helper.
 *
 * The Google OAuth redirect URI MUST first be allowlisted with the Google OAuth
 * client, and aegis-pentest-eg.vercel.app must be in Firebase Authorized domains.
 * Do not enable this flag as part of a routine UI deployment.
 */
export const AEGIS_AUTH_HOST='aegis-pentest-eg.vercel.app';

export function helperProject(env:NodeJS.ProcessEnv):string|null {
 if(env.NEXT_PUBLIC_AEGIS_FIREBASE_FIRST_PARTY!=='true')return null;
 const project=env.NEXT_PUBLIC_AEGIS_FIREBASE_HELPER_PROJECT_ID||'';
 if(!/^[a-z][a-z0-9-]{5,62}$/.test(project)||project.endsWith('-'))return null;
 return project;
}

export function firstPartyFirebaseConfig<T extends FirebaseOptions>(
 config:T, hostname:string, env:NodeJS.ProcessEnv
):T {
 const project=helperProject(env);
 if(!project||hostname!==AEGIS_AUTH_HOST||config.projectId!==project)return config;
 return {...config,authDomain:AEGIS_AUTH_HOST};
}
