// Pocitadlo sestaveni shaderu (glLinkProgram) pro mereni zaseku na PC: gcc -shared -fPIC -O2 -o build/glcount.so tools/glcount.c -ldl
// pak LD_PRELOAD=build/glcount.so; kazde sestaveni = radek GLLINK na stderr (main.gd TVRZ_PRVNI pise ZNACKA mezi mista)
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <stdlib.h>
typedef void (*fn_u)(unsigned);
typedef void *(*gpa_t)(const unsigned char *);
typedef void *(*dlsym_t)(void *, const char *);
static dlsym_t real_dlsym;
static gpa_t real_gpa;
static fn_u real_link, real_comp;
static unsigned long n_link, n_comp;
static double ms(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec*1e3+t.tv_nsec/1e6;}
typedef void (*gas_t)(unsigned, int, int *, unsigned *);
typedef void (*gss_t)(unsigned, int, int *, char *);
static gas_t p_gas; static gss_t p_gss;
static char src[1 << 20];
/* popis programu: definice varianty (#define), otisk zdroje bez definic a prvni cleny bloku MaterialUniforms
   (poznat, ktery shader/varianta se sestavuje) */
static void popis(unsigned p, char *out, int max){
  out[0] = 0;
  if(!p_gas){ p_gas=(gas_t)real_gpa((const unsigned char*)"glGetAttachedShaders"); p_gss=(gss_t)real_gpa((const unsigned char*)"glGetShaderSource"); }
  if(!p_gas||!p_gss) return;
  unsigned sh[4]; int n=0; p_gas(p,4,&n,sh);
  unsigned long h=1469598103934665603UL; int vblok=0, clenu=0;
  for(int i=0;i<n;i++){ int len=0; p_gss(sh[i],sizeof(src),&len,src);
    for(char *l=src; l && *l; ){ char *e=strchr(l,'\n'); if(e)*e=0;
      if(i==0 && !strncmp(l,"#define ",8)){ if((int)(strlen(out)+strlen(l))<max-2){ strcat(out,l+8); strcat(out,"|"); } }
      else { for(char *c=l;*c;c++){ h^=(unsigned char)*c; h*=1099511628211UL; } }
      if(strstr(l,"uniform MaterialUniforms")) vblok=1;
      else if(vblok && strchr(l,'}')) vblok=0;
      else if(vblok && i==0 && clenu<4 && strchr(l,';')){ clenu++; if((int)(strlen(out)+strlen(l))<max-2){ strcat(out,"~"); strcat(out,l); } }
      if(e){*e='\n'; l=e+1;} else break; }
  }
  char hb[32]; snprintf(hb,sizeof hb," #%08lx",h&0xffffffffUL); if((int)strlen(out)<max-20) strcat(out,hb);
}
static char pop[8192];
static void w_link(unsigned p){double t=ms();real_link(p);n_link++;double d=ms()-t;
  if(getenv("GLCOUNT_POPIS")){popis(p,pop,sizeof(pop));fprintf(stderr,"GLLINK %lu %.1f ms %s\n",n_link,d,pop);}
  else fprintf(stderr,"GLLINK %lu %.1f ms\n",n_link,d);}
static void w_comp(unsigned s){double t=ms();real_comp(s);n_comp++;}
static void *wrap(const char *name, void *f){
  if(!f) return f;
  if(!strcmp(name,"glLinkProgram")){real_link=(fn_u)f;return (void*)w_link;}
  if(!strcmp(name,"glCompileShader")){real_comp=(fn_u)f;return (void*)w_comp;}
  return f;}
static void *w_gpa(const unsigned char *n){return wrap((const char*)n, real_gpa(n));}
static void init(void){ if(!real_dlsym) real_dlsym=(dlsym_t)dlvsym(RTLD_NEXT,"dlsym","GLIBC_2.34"); if(!real_dlsym) real_dlsym=(dlsym_t)dlvsym(RTLD_NEXT,"dlsym","GLIBC_2.2.5");}
void *dlsym(void *h, const char *name){
  init();
  void *f=real_dlsym(h,name);
  if(f && (!strcmp(name,"glXGetProcAddressARB")||!strcmp(name,"glXGetProcAddress"))){real_gpa=(gpa_t)f;return (void*)w_gpa;}
  return wrap(name,f);}
