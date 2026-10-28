import {it,expect} from 'vitest';
import {apiOrigin} from '../lib/deployment';
it('fails a Vercel build with a missing or local backend instead of publishing a disconnected UI',()=>{
 for(const value of [undefined,'http://localhost:8000','https://user:secret@example.com','https://api.example.com/path']){
  expect(()=>apiOrigin({VERCEL:'1',API_INTERNAL_URL:value,NODE_ENV:'production'})).toThrow();
 }
});
it('accepts the deployed HTTPS API and normalizes a trailing slash',()=>{
 expect(apiOrigin({VERCEL:'1',API_INTERNAL_URL:'https://api.example.com/',NODE_ENV:'production'})).toBe('https://api.example.com');
});
