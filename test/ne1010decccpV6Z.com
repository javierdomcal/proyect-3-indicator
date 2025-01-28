%chk=ne1010decccpV6Z.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(10,10)/dec-cc-pV6Z gfinput fchk=all density=current iop(5/33=1) iop(4/21=100) out=wfx

ne1010decccpV6Z neon CASSCF(10,10) dec-cc-pV6Z

0 1
Ne 0.0 0.0 0.0

ne1010decccpV6Z.wfx
