

/**************************************************

compile with the command: gcc read_rx.c rs232.c -Wall -Wextra \-o2 -o read_rx

**************************************************/

#include <stdlib.h>
#include <stdio.h>
#include <sys/time.h>
#include <time.h>

#ifdef _WIN32
#include <Windows.h>
#else
#include <unistd.h>
#endif

#include "rs232.h"


double decodeTemperature(unsigned int rbuf);
double decodeHumidity(unsigned int rbuf, double temperature_ref);

int main(int argc, char *argv[])
{

    struct tm *gmp;
    struct tm gm; 
    time_t t, t0;
    int ty, tmon, tday, thour, tmin, tsec, time_acq_h_MAX;
    float time_acq_h;
    int i, n, nloc, InitFlag, StartFlag, nhit, hit, trg,
    cport_nr=17,   
    bdrate=....;  

  int cnt=0;
  FILE *file;
  FILE *currN; //file that stores current run name to be used by external programs
  double val_temp, val_hum;
  unsigned char buf[4096],sht75_nblab02__frame[4];
  unsigned int val_temp_int, val_hum_int;
  char NameF[100];

  char mode[]={'8','N','1',0};
 
// t0 per lo start del run
  t0 = time(NULL);
  gmp = gmtime(&t0);
    if (gmp == NULL)
      printf("error on gmp");

   gm = *gmp;   

  ty=gm.tm_year+1900;
  tmon=gm.tm_mon+1;
  tday=gm.tm_mday;
  thour=gm.tm_hour+1;
  tmin=gm.tm_min;
  tsec=gm.tm_sec;

  if (argv[1] == NULL)
       {
             printf("format: read_rx Numero di ore di acquisizione \n");
             return -1;
       }        
   else
       { 
            time_acq_h_MAX = atoi(argv[1]);
            sprintf(NameF,"sht75_nblab02__Hum_Temp_RUN_%04d%02d%02d%02d%02d%02d_%d_h.txt",ty,tmon,tday,thour,tmin,tsec,time_acq_h_MAX);
            printf("file_open %s --> durata in ore %d\n",NameF,time_acq_h_MAX);
            file = fopen(NameF, "w+" );
       }
 
        //writing the file name to the current run name file to be read and used by external programs
        //-------------------------------------------------------------------------------------------
        
        
        currN = fopen("currN.txt", "w");                         //creato il primo, cambiare w con a+
        fprintf(currN, "\n");
        fprintf(currN, NameF);
        fclose (currN);
        //-------------------------------------------------------------------------------------------


 

  if(RS232_OpenComport(cport_nr, bdrate, mode))
  {
    printf("Can not open comport\n");

    return(0);
  }


  InitFlag=0;
  nloc=0;
  trg=0;
  while(1)
  {
    n = RS232_PollComport(cport_nr, buf, 4095);
 
      // tempo evento
      t = time(NULL);
      gmp = gmtime(&t);
      if (gmp == NULL)
        printf("error on gmp");
      printf("%d %d ", cnt, n);

      gm = *gmp;   
     


      time_acq_h=(t-t0);
     
     printf("time diff: %ld (sec) \n",time_acq_h);
     if (time_acq_h> time_acq_h_MAX*3600)
        {
          printf(" time_duration RUN in hours > %d \n",time_acq_h_MAX); 
          break;
        }  
     else
        {
          if (cnt%100==0) 
            printf(" time current in hour %f \n",(float)time_acq_h/3600.);
        }
    if(n > 0)
    {

   /*

   METTERE IL CODICE di DECODIFICA FRAME

    */

     printf("cnt %d received %i bytes \n", cnt, n);
     cnt++;
    }

#ifdef _WIN32
    Sleep(100);
#else
    usleep(1000000); 
#endif
  }
 
  fclose (file);

  return(0);
}



double decodeTemperature(unsigned int rbuf) {
/*
......
decodificare il valore letto dal sensore
*/
 }

double decodeHumidity(unsigned int rbuf, double temperature_ref){
/*
......
decodificare il valore letto dal sensore
*/
}