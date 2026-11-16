import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { InputLock, MAX_SEQUENCE_MS } from '../../src/core/sequencer/input-lock';

function createControlledSequence(): { sequence: () => Promise<void>; finish: () => void } {
  let finish = (): void => {};
  const done = new Promise<void>((resolve) => {
    finish = resolve;
  });
  return { sequence: () => done, finish };
}

describe('InputLock', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('runs a sequence when idle and reports it as accepted', async () => {
    const lock = new InputLock();
    const sequence = vi.fn(() => Promise.resolve());

    const isAccepted = await lock.run(sequence);

    expect(isAccepted).toBe(true);
    expect(sequence).toHaveBeenCalledOnce();
  });

  it('drops input that arrives while a sequence is playing', async () => {
    const lock = new InputLock();
    const first = createControlledSequence();
    const second = vi.fn(() => Promise.resolve());
    const firstRun = lock.run(first.sequence);

    const isSecondAccepted = await lock.run(second);
    first.finish();
    await firstRun;

    expect(isSecondAccepted).toBe(false);
    expect(second).not.toHaveBeenCalled();
  });

  it('accepts new input after the previous sequence finishes', async () => {
    const lock = new InputLock();
    await lock.run(() => Promise.resolve());

    const isAccepted = await lock.run(() => Promise.resolve());

    expect(isAccepted).toBe(true);
    expect(lock.isBusy).toBe(false);
  });

  it('releases the lock after the timeout when a sequence never finishes', async () => {
    const lock = new InputLock();
    const stuck = createControlledSequence();
    const run = lock.run(stuck.sequence);
    expect(lock.isBusy).toBe(true);

    await vi.advanceTimersByTimeAsync(MAX_SEQUENCE_MS);

    await expect(run).resolves.toBe(true);
    expect(lock.isBusy).toBe(false);
  });

  it('releases the lock and rethrows when a sequence fails', async () => {
    const lock = new InputLock();
    const failure = new Error('audio failed');

    await expect(lock.run(() => Promise.reject(failure))).rejects.toBe(failure);

    expect(lock.isBusy).toBe(false);
  });

  it.each([0, -1, Number.NaN, Number.POSITIVE_INFINITY])(
    'rejects an invalid timeout of %s',
    (invalidTimeout) => {
      expect(() => new InputLock(invalidTimeout)).toThrow(RangeError);
    },
  );
});
