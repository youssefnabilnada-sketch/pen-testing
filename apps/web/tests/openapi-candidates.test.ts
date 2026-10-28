import {describe, expect, it} from 'vitest';
import {getOpenApiCandidates, isSafeCandidatePath} from '../lib/openapi-candidates';

describe('bounded user-reviewed OpenAPI GET candidate import', () => {
  it('suggests public plain GET endpoints and never authorizes them', () => {
    const input = {openapi:'3.1.0', paths: {
      '/api/health':{get:{responses:{'200':{description:'OK'}}}},
      '/account/logout':{get:{}}, '/admin/users':{get:{}}, '/x/../danger':{get:{}},
      '/api/{userId}':{get:{}}, '/search?query=x':{get:{}}, '/a%2fb':{get:{}}, '/invalid-security':{get:{security:{}}},
      '/public':{post:{}}, '/legacy':{$ref:'#/paths/other',get:{}},
      '/private':{get:{security:[{apiKey:[]}]}}
    }};
    expect(getOpenApiCandidates(input)).toEqual(['/api/health']);
  });
  it('honors a document-wide authentication requirement and operation public override', () => {
    expect(getOpenApiCandidates({openapi:'3.0.3', security:[{apiKey:[]}],paths:{
      '/private':{get:{}}, '/public':{get:{security:[]}}
    }})).toEqual(['/public']);
  });
  it('excludes paths with required, unresolved or non-query parameters and server overrides', () => {
    expect(getOpenApiCandidates({openapi:'3.1.1',paths:{
      '/ok':{get:{parameters:[{in:'query',name:'format',required:false}]}},
      '/required-query':{get:{parameters:[{in:'query',name:'id',required:true}]}},
      '/required-path-level':{parameters:[{in:'header',name:'Authorization',required:true}],get:{}},
      '/unresolved-ref':{parameters:[{$ref:'#/components/parameters/access'}],get:{}},
      '/invalid-parameters':{get:{parameters:{name:'x'}}},
      '/cookie':{get:{parameters:[{in:'cookie',name:'session',required:false}]}},
      '/override-host':{servers:[{url:'https://external.example'}],get:{}},
      '/override-operation':{get:{servers:[{url:'https://external.example'}]}},
      '/auth-required':{get:{security:[{bearer:[]}]}}
    }})).toEqual(['/ok']);
  });
  it('rejects OpenAPI root server mismatch, unknown variables and base paths', () => {
    const input = {openapi:'3.1.0', paths:{'/health':{get:{}}}};
    expect(getOpenApiCandidates({...input,servers:[{url:'https://api.example.test'}]},'https://api.example.test')).toEqual(['/health']);
    expect(getOpenApiCandidates({...input,servers:[{url:'/'}]},'https://api.example.test')).toEqual(['/health']);
    for (const servers of [
      [{url:'https://wrong.example.test'}],
      [{url:'https://api.example.test/v1'}],
      [{url:'https://api.example.test?key=1'}],
      [{url:'https://api.example.test/#fragment'}],
      [{url:'https://{hostname}.example.test',variables:{hostname:{default:'api'}}}],
      [{url:'https://api.example.test'},{url:'https://other.example.test'}],
      [], 'not-an-array'
    ]) {
      expect(() => getOpenApiCandidates({...input,servers},'https://api.example.test')).toThrow();
    }
    expect(() => getOpenApiCandidates({...input,servers:[{url:'https://api.example.test'}]})).toThrow();
  });
  it('fails closed on malformed documents and excessive candidates', () => {
    for (const invalid of [null, [], {openapi:'3.0.1',paths:null}, {openapi:'2.0',paths:{}},
      {openapi:'3.0.0', paths:{'/delete':{get:{}}}},
      {openapi:'3.1.0',paths:Object.fromEntries(Array.from({length:21},(_,i)=>['/api/p'+i,{get:{}}]))}]) {
      expect(() => getOpenApiCandidates(invalid)).toThrow();
    }
    expect(isSafeCandidatePath('/api/health')).toBe(true);
    for (const path of ['/logout', '/Admin/x', '/a/../b', '/a/%2e', '/a?x=1', '//host', '/foo\\bar', '/api/restart', '/password/reset', '/api/token', '/api/logout-v2', '/account_disable', '/billing.refund']) {
      expect(isSafeCandidatePath(path)).toBe(false);
    }
  });
});
