import {render,screen,fireEvent,cleanup,act} from '@testing-library/react';
import {afterEach,it,expect,vi} from 'vitest';
import Retry from '../app/console/VerificationRetry';
afterEach(()=>{cleanup();vi.useRealTimers()});
it('is opt-in, bounded to three requests, and never launches assessments',async()=>{
 vi.useFakeTimers();const api=vi.fn(async()=>{throw new Error('Token not visible yet')});const done=vi.fn(async()=>{});
 render(<Retry assetId="a" challengeId="c" api={api} onRunning={vi.fn()} onVerified={done}/>);
 await act(async()=>{await vi.advanceTimersByTimeAsync(90000)});expect(api).not.toHaveBeenCalled();
 fireEvent.click(screen.getByRole('button',{name:'Retry ownership automatically'}));
 await act(async()=>{await vi.advanceTimersByTimeAsync(150000)});
 expect(api).toHaveBeenCalledTimes(3);expect(api).toHaveBeenLastCalledWith('/assets/a/verify/c','POST');expect(done).not.toHaveBeenCalled();expect(screen.getByRole('button',{name:'Retry ownership automatically'})).toBeTruthy();
});
it('stops after verified success and invokes the existing refresh only',async()=>{
 vi.useFakeTimers();const api=vi.fn(async()=>({message:'verified'})),done=vi.fn(async()=>{});
 render(<Retry assetId="a" challengeId="c" api={api} onRunning={vi.fn()} onVerified={done}/>);fireEvent.click(screen.getByRole('button',{name:'Retry ownership automatically'}));
 await act(async()=>{await vi.advanceTimersByTimeAsync(150000)});expect(api).toHaveBeenCalledTimes(1);expect(done).toHaveBeenCalledOnce();expect(screen.getByText(/No assessment was started/)).toBeTruthy();
});
it('cancels pending attempts when stopped or unmounted',async()=>{
 vi.useFakeTimers();const api=vi.fn(async()=>({}));const {unmount}=render(<Retry assetId="a" challengeId="c" api={api} onRunning={vi.fn()} onVerified={vi.fn()}/>);
 fireEvent.click(screen.getByRole('button',{name:'Retry ownership automatically'}));fireEvent.click(screen.getByRole('button',{name:'Stop automatic checks'}));await act(async()=>{await vi.advanceTimersByTimeAsync(60000)});expect(api).not.toHaveBeenCalled();
 fireEvent.click(screen.getByRole('button',{name:'Retry ownership automatically'}));unmount();await act(async()=>{await vi.advanceTimersByTimeAsync(60000)});expect(api).not.toHaveBeenCalled();
});
it('does not retry a consumed proof when only workspace refresh fails',async()=>{
 vi.useFakeTimers();const api=vi.fn(async()=>({message:'verified'}));
 render(<Retry assetId="a" challengeId="c" api={api} onRunning={vi.fn()} onVerified={async()=>{throw new Error('refresh failed')}}/>);
 fireEvent.click(screen.getByRole('button',{name:'Retry ownership automatically'}));await act(async()=>{await vi.advanceTimersByTimeAsync(150000)});
 expect(api).toHaveBeenCalledTimes(1);expect(screen.getByText(/workspace refresh failed/)).toBeTruthy();
});
it('ignores a verification response arriving after cancellation',async()=>{
 vi.useFakeTimers();let finish!:(v:unknown)=>void;const response=new Promise(resolve=>{finish=resolve});const done=vi.fn(async()=>{});
 render(<Retry assetId="a" challengeId="c" api={()=>response} onRunning={vi.fn()} onVerified={done}/>);
 fireEvent.click(screen.getByRole('button',{name:'Retry ownership automatically'}));await act(async()=>{await vi.advanceTimersByTimeAsync(30000)});
 fireEvent.click(screen.getByRole('button',{name:'Stop automatic checks'}));await act(async()=>{finish({message:'verified'});await response;});
 expect(done).not.toHaveBeenCalled();expect(screen.queryByText('Ownership verified. No assessment was started.')).toBeNull();
});
